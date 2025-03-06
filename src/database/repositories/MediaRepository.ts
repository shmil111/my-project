import { BaseRepository } from './BaseRepository';
import { DatabaseRecord } from '../../services/DatabaseService';
import { databaseConfig } from '../config/database.config';
import { User } from './UserRepository';
import { Post } from './PostRepository';
import { promisify } from 'util';
import { exec } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as sharp from 'sharp';
import { v4 as uuidv4 } from 'uuid';

const execAsync = promisify(exec);

export interface Media extends DatabaseRecord {
  userId: number;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  path: string;
  url: string;
  alt?: string;
  caption?: string;
  metadata?: Record<string, any>;
  width?: number;
  height?: number;
  duration?: number;
  isPublic: boolean;
  status: 'processing' | 'ready' | 'error' | 'optimizing';
  errorMessage?: string;
  processingProgress?: number;
  variants?: Record<string, {
    path: string;
    url: string;
    width?: number;
    height?: number;
    size: number;
    format: string;
    quality: number;
  }>;
  tags?: string[];
  location?: {
    latitude: number;
    longitude: number;
    place?: string;
  };
  exif?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

export interface PostMedia {
  postId: number;
  mediaId: number;
  type: 'attachment' | 'featured' | 'gallery' | 'thumbnail';
  order: number;
  createdAt: Date;
}

export interface MediaWithRelations extends Media {
  user: User;
  posts: Array<{
    post: Post;
    type: PostMedia['type'];
    order: number;
  }>;
}

export interface MediaProcessingOptions {
  generateThumbnails?: boolean;
  optimize?: boolean;
  extractMetadata?: boolean;
  generateWebP?: boolean;
  quality?: number;
  maxWidth?: number;
  maxHeight?: number;
  preserveAspectRatio?: boolean;
}

export interface MediaQueryOptions {
  userId?: number;
  mimeType?: string;
  isPublic?: boolean;
  status?: Media['status'];
  startDate?: Date;
  endDate?: Date;
  searchTerm?: string;
  sortBy?: keyof Media;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
  tags?: string[];
  location?: {
    latitude: number;
    longitude: number;
    radius: number; // in kilometers
  };
}

export class MediaRepository extends BaseRepository<Media> {
  private readonly processingQueue: Map<number | string, MediaProcessingOptions> = new Map();
  private readonly cache: Map<string, { data: any; expires: number }> = new Map();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  constructor() {
    super('media', databaseConfig);
  }

  /**
   * Process media file with advanced options
   */
  async processMedia(id: number | string, options: MediaProcessingOptions): Promise<Media & { id: number | string }> {
    const media = await this.getById(id);
    if (!media) {
      throw new Error('Media not found');
    }

    await this.updateProcessingStatus(id, 'processing', 0);

    try {
      // Extract metadata if requested
      if (options.extractMetadata) {
        await this.extractMetadata(media);
      }

      // Generate variants if needed
      if (options.generateThumbnails || options.optimize || options.generateWebP) {
        await this.generateVariants(media, options);
      }

      // Update status to ready
      return this.updateProcessingStatus(id, 'ready', 100);
    } catch (error) {
      return this.updateProcessingStatus(id, 'error', undefined, error.message);
    }
  }

  /**
   * Extract metadata from media file
   */
  private async extractMetadata(media: Media): Promise<void> {
    const metadata: Record<string, any> = {};
    
    try {
      if (media.mimeType.startsWith('image/')) {
        const image = sharp(media.path);
        const metadata = await image.metadata();
        
        // Extract EXIF data if available
        if (metadata.exif) {
          const exif = await this.extractExif(media.path);
          metadata.exif = exif;
        }

        // Extract GPS data if available
        if (metadata.exif?.GPSLatitude && metadata.exif?.GPSLongitude) {
          metadata.location = {
            latitude: this.convertGPSCoordinate(metadata.exif.GPSLatitude),
            longitude: this.convertGPSCoordinate(metadata.exif.GPSLongitude),
            place: await this.reverseGeocode(metadata.exif.GPSLatitude, metadata.exif.GPSLongitude)
          };
        }
      } else if (media.mimeType.startsWith('video/')) {
        const { stdout } = await execAsync(`ffprobe -v quiet -print_format json -show_format -show_streams "${media.path}"`);
        metadata.ffprobe = JSON.parse(stdout);
      }

      await this.update(media.id, { metadata });
    } catch (error) {
      console.error('Error extracting metadata:', error);
    }
  }

  /**
   * Generate media variants
   */
  private async generateVariants(media: Media, options: MediaProcessingOptions): Promise<void> {
    const variants: Media['variants'] = {};
    const image = sharp(media.path);

    // Generate thumbnail
    if (options.generateThumbnails) {
      const thumbnailPath = path.join(path.dirname(media.path), `thumb_${path.basename(media.path)}`);
      await image
        .resize(150, 150, { fit: 'cover' })
        .toFile(thumbnailPath);
      
      variants.thumbnail = {
        path: thumbnailPath,
        url: this.generateUrl(thumbnailPath),
        width: 150,
        height: 150,
        size: fs.statSync(thumbnailPath).size,
        format: path.extname(thumbnailPath).slice(1),
        quality: 80
      };
    }

    // Generate optimized version
    if (options.optimize) {
      const optimizedPath = path.join(path.dirname(media.path), `opt_${path.basename(media.path)}`);
      await image
        .resize(options.maxWidth, options.maxHeight, {
          fit: options.preserveAspectRatio ? 'inside' : 'fill'
        })
        .jpeg({ quality: options.quality || 80 })
        .toFile(optimizedPath);

      variants.optimized = {
        path: optimizedPath,
        url: this.generateUrl(optimizedPath),
        width: options.maxWidth,
        height: options.maxHeight,
        size: fs.statSync(optimizedPath).size,
        format: 'jpeg',
        quality: options.quality || 80
      };
    }

    // Generate WebP version
    if (options.generateWebP) {
      const webpPath = path.join(path.dirname(media.path), `${path.basename(media.path, path.extname(media.path))}.webp`);
      await image
        .webp({ quality: options.quality || 80 })
        .toFile(webpPath);

      variants.webp = {
        path: webpPath,
        url: this.generateUrl(webpPath),
        size: fs.statSync(webpPath).size,
        format: 'webp',
        quality: options.quality || 80
      };
    }

    await this.update(media.id, { variants });
  }

  /**
   * Extract EXIF data from image
   */
  private async extractExif(filePath: string): Promise<Record<string, any>> {
    try {
      const { stdout } = await execAsync(`exiftool -json "${filePath}"`);
      return JSON.parse(stdout)[0];
    } catch (error) {
      console.error('Error extracting EXIF:', error);
      return {};
    }
  }

  /**
   * Convert GPS coordinates from EXIF format
   */
  private convertGPSCoordinate(coordinate: string): number {
    const parts = coordinate.split(' ');
    const degrees = parseFloat(parts[0]);
    const minutes = parseFloat(parts[1]);
    const seconds = parseFloat(parts[2]);
    const direction = parts[3];
    
    let decimal = degrees + minutes / 60 + seconds / 3600;
    if (direction === 'S' || direction === 'W') {
      decimal = -decimal;
    }
    
    return decimal;
  }

  /**
   * Reverse geocode coordinates to get place name
   */
  private async reverseGeocode(latitude: number, longitude: number): Promise<string | undefined> {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
      );
      const data = await response.json();
      return data.display_name;
    } catch (error) {
      console.error('Error reverse geocoding:', error);
      return undefined;
    }
  }

  /**
   * Generate URL for media file
   */
  private generateUrl(filePath: string): string {
    const relativePath = path.relative(process.env.MEDIA_ROOT || 'uploads', filePath);
    return `${process.env.MEDIA_URL || '/media'}/${relativePath.replace(/\\/g, '/')}`;
  }

  /**
   * Add tags to media
   */
  async addTags(id: number | string, tags: string[]): Promise<Media & { id: number | string }> {
    const media = await this.getById(id);
    if (!media) {
      throw new Error('Media not found');
    }

    const existingTags = media.tags || [];
    const newTags = [...new Set([...existingTags, ...tags])];

    return this.update(id, { tags: newTags });
  }

  /**
   * Remove tags from media
   */
  async removeTags(id: number | string, tags: string[]): Promise<Media & { id: number | string }> {
    const media = await this.getById(id);
    if (!media) {
      throw new Error('Media not found');
    }

    const existingTags = media.tags || [];
    const newTags = existingTags.filter(tag => !tags.includes(tag));

    return this.update(id, { tags: newTags });
  }

  /**
   * Find media by tags
   */
  async findByTags(tags: string[]): Promise<Media[]> {
    const query = `
      SELECT m.*
      FROM media m
      WHERE JSON_CONTAINS(m.tags, ?)
      ORDER BY m.createdAt DESC
    `;
    return this.rawQuery(query, [JSON.stringify(tags)]);
  }

  /**
   * Find media by location
   */
  async findByLocation(latitude: number, longitude: number, radius: number): Promise<Media[]> {
    const query = `
      SELECT m.*,
             ST_Distance_Sphere(
               point(m.location->>'$.longitude', m.location->>'$.latitude'),
               point(?, ?)
             ) as distance
      FROM media m
      WHERE ST_Distance_Sphere(
        point(m.location->>'$.longitude', m.location->>'$.latitude'),
        point(?, ?)
      ) <= ?
      ORDER BY distance
    `;
    return this.rawQuery(query, [longitude, latitude, longitude, latitude, radius * 1000]);
  }

  /**
   * Get media statistics with advanced metrics
   */
  async getMediaStats(): Promise<{
    total: number;
    byType: Record<string, number>;
    byStatus: Record<string, number>;
    byTag: Record<string, number>;
    totalSize: number;
    averageSize: number;
    storageUsage: {
      total: number;
      byType: Record<string, number>;
      byVariant: Record<string, number>;
    };
    processingStats: {
      success: number;
      failed: number;
      inProgress: number;
      averageProcessingTime: number;
    };
  }> {
    const query = `
      SELECT 
        COUNT(*) as total,
        mimeType,
        status,
        SUM(size) as total_size,
        AVG(size) as avg_size,
        GROUP_CONCAT(DISTINCT tags) as all_tags,
        COUNT(CASE WHEN status = 'ready' THEN 1 END) as success_count,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_count,
        COUNT(CASE WHEN status = 'processing' THEN 1 END) as in_progress_count,
        AVG(TIMESTAMPDIFF(SECOND, createdAt, updatedAt)) as avg_processing_time
      FROM media
      GROUP BY mimeType, status
    `;
    const results = await this.rawQuery(query);

    const stats = {
      total: 0,
      byType: {} as Record<string, number>,
      byStatus: {} as Record<string, number>,
      byTag: {} as Record<string, number>,
      totalSize: 0,
      averageSize: 0,
      storageUsage: {
        total: 0,
        byType: {} as Record<string, number>,
        byVariant: {} as Record<string, number>
      },
      processingStats: {
        success: 0,
        failed: 0,
        inProgress: 0,
        averageProcessingTime: 0
      }
    };

    results.forEach((row: any) => {
      stats.total += row.total;
      stats.byType[row.mimeType] = row.total;
      stats.byStatus[row.status] = row.total;
      stats.totalSize += row.total_size;
      stats.averageSize = row.avg_size;

      // Process tags
      if (row.all_tags) {
        const tags = JSON.parse(`[${row.all_tags}]`);
        tags.forEach((tag: string) => {
          stats.byTag[tag] = (stats.byTag[tag] || 0) + 1;
        });
      }

      // Process storage usage
      stats.storageUsage.total += row.total_size;
      stats.storageUsage.byType[row.mimeType] = (stats.storageUsage.byType[row.mimeType] || 0) + row.total_size;

      // Process processing stats
      stats.processingStats.success += row.success_count;
      stats.processingStats.failed += row.failed_count;
      stats.processingStats.inProgress += row.in_progress_count;
      stats.processingStats.averageProcessingTime = row.avg_processing_time;
    });

    return stats;
  }

  /**
   * Clean up orphaned media and variants
   */
  async cleanupOrphanedMedia(): Promise<{ deleted: number; freed: number }> {
    // Delete orphaned media records
    const query = `
      DELETE FROM media m
      WHERE NOT EXISTS (
        SELECT 1 FROM post_media pm
        WHERE pm.mediaId = m.id
      )
    `;
    const result = await this.rawQuery(query);
    const deleted = result.affectedRows || 0;

    // Clean up orphaned files
    const mediaDir = process.env.MEDIA_ROOT || 'uploads';
    let freed = 0;

    const files = await fs.promises.readdir(mediaDir);
    for (const file of files) {
      const filePath = path.join(mediaDir, file);
      const stats = await fs.promises.stat(filePath);
      
      if (stats.isFile()) {
        const media = await this.findByFilename(file);
        if (!media) {
          await fs.promises.unlink(filePath);
          freed += stats.size;
        }
      }
    }

    return { deleted, freed };
  }

  /**
   * Find media by filename
   */
  private async findByFilename(filename: string): Promise<Media | null> {
    const query = `
      SELECT m.*
      FROM media m
      WHERE m.filename = ?
      LIMIT 1
    `;
    const results = await this.rawQuery(query, [filename]);
    return results[0] || null;
  }

  private async getFromCache(key: string): Promise<Media[] | null> {
    const cached = this.cache.get(key);
    if (cached && cached.expires > Date.now()) {
      return cached.data;
    }
    return null;
  }

  private async setCache(key: string, data: Media[]): Promise<void> {
    this.cache.set(key, {
      data,
      expires: Date.now() + this.CACHE_TTL
    });
  }
} 