import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

TWO = len("ab")
FIVE = len("apple")
TWELVE = len("abcdefghijkl")
EIGHT = len("abcdefgh")
FIFTY = len("abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwx")

def analyze_project_structure(csv_path):
    """Analyze project structure from CSV file"""
    project_data = pd.read_csv(csv_path)
    project_summary = {
        "total_files": len(project_data),
        "total_size": project_data["size"].sum(),
        "languages": project_data["type"].value_counts(),
        "largest_files": project_data.nlargest(FIVE, "size")[["name", "size"]]
    }
    visualize_project_metrics(project_data)
    return project_summary

def visualize_project_metrics(data):
    """Create visualizations of project metrics"""
    fig, axs = plt.subplots(TWO, TWO, figsize=(TWELVE, EIGHT))
    data["type"].value_counts().plot.pie(ax=axs[0, 0], title="Language Distribution")
    ax_hist = axs[0, 1]
    sns.histplot(data=data, x="size", bins=FIFTY, ax=ax_hist)
    ax_hist.set_title("File Size Distribution")
    data.groupby("folder")["size"].sum().plot(kind="bar", ax=axs[1, 0], title="Size by Folder")
    plt.tight_layout()
    plt.show()

def main():
    csv_path = "myproject.csv"
    if not os.path.exists(csv_path):
        print("Error: Could not find myproject.csv")
        return
    project_metrics = analyze_project_structure(csv_path)
    print("\n✨ Project Analysis Results ✨")
    print(f"\n📊 Total Files: {project_metrics['total_files']}")
    print(f"📏 Total Size: {project_metrics['total_size']} bytes")
    print("\n💻 Language Distribution:")
    print(project_metrics["languages"])
    print("\n📄 Largest Files:")
    print(project_metrics["largest_files"])

if __name__ == "__main__":
    main()
