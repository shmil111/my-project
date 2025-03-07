"""
Documentation Rephraser - Analyzes and improves document clarity and consistency.
"""
import re
import spacy
from typing import Dict, List, Tuple
from collections import defaultdict
import textstat
from transformers import pipeline
from nltk.tokenize import sent_tokenize
import yaml

class DocRephraser:
    def __init__(self):
        """Initialize the document rephraser."""
        # Load language models
        self.nlp = spacy.load("en_core_web_sm")
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        
        # Load style guides
        self.style_guide = self._load_style_guide()
        
        # Initialize improvement trackers
        self.suggestions = defaultdict(list)
        self.metrics = {}
        
    def _load_style_guide(self) -> Dict:
        """Load writing style guidelines."""
        default_guide = {
            "preferred_terms": {
                "utilize": "use",
                "implement": "create",
                "leverage": "use",
                "facilitate": "help",
                "in order to": "to",
                "commence": "start",
                "terminate": "end",
                "prior to": "before",
                "subsequent to": "after",
                "regarding": "about"
            },
            "sentence_length": {
                "max": 25,
                "preferred": 15
            },
            "paragraph_length": {
                "max": 150,
                "preferred": 75
            },
            "readability": {
                "min_score": 60,  # Flesch Reading Ease
                "target_score": 70
            },
            "voice": "active",
            "technical_level": "intermediate"
        }
        
        try:
            with open("style_guide.yaml", "r") as f:
                custom_guide = yaml.safe_load(f)
                return {**default_guide, **custom_guide}
        except FileNotFoundError:
            return default_guide
    
    def analyze_document(self, content: str) -> Dict:
        """Analyze document for potential improvements."""
        doc = self.nlp(content)
        
        analysis = {
            "metrics": self._calculate_metrics(content),
            "suggestions": {
                "word_choice": self._analyze_word_choice(doc),
                "sentence_structure": self._analyze_sentences(doc),
                "clarity": self._analyze_clarity(doc),
                "technical_terms": self._analyze_technical_terms(doc),
                "consistency": self._analyze_consistency(doc)
            },
            "summary": self._generate_summary(content)
        }
        
        return analysis
    
    def _calculate_metrics(self, content: str) -> Dict:
        """Calculate readability and complexity metrics."""
        return {
            "readability_score": textstat.flesch_reading_ease(content),
            "grade_level": textstat.coleman_liau_index(content),
            "sentence_count": len(sent_tokenize(content)),
            "avg_sentence_length": len(content.split()) / len(sent_tokenize(content)),
            "complex_word_percentage": textstat.difficult_words_rate(content)
        }
    
    def _analyze_word_choice(self, doc) -> List[Dict]:
        """Analyze and suggest word choice improvements."""
        suggestions = []
        
        for token in doc:
            # Check against preferred terms
            if token.text.lower() in self.style_guide["preferred_terms"]:
                suggestions.append({
                    "original": token.text,
                    "suggestion": self.style_guide["preferred_terms"][token.text.lower()],
                    "reason": "Preferred term",
                    "context": token.sent.text
                })
            
            # Check for overly complex words
            if len(token.text) > 12 and token.pos_ == "VERB":
                suggestions.append({
                    "original": token.text,
                    "suggestion": f"Consider a simpler verb",
                    "reason": "Complex word",
                    "context": token.sent.text
                })
        
        return suggestions
    
    def _analyze_sentences(self, doc) -> List[Dict]:
        """Analyze sentence structure and length."""
        suggestions = []
        
        for sent in doc.sents:
            # Check sentence length
            if len(sent) > self.style_guide["sentence_length"]["max"]:
                suggestions.append({
                    "original": sent.text,
                    "suggestion": "Consider breaking this sentence into smaller parts",
                    "reason": "Long sentence",
                    "length": len(sent)
                })
            
            # Check for passive voice
            if self._is_passive(sent) and self.style_guide["voice"] == "active":
                suggestions.append({
                    "original": sent.text,
                    "suggestion": "Consider using active voice",
                    "reason": "Passive voice",
                    "context": sent.text
                })
        
        return suggestions
    
    def _analyze_clarity(self, doc) -> List[Dict]:
        """Analyze overall clarity and comprehension."""
        suggestions = []
        
        # Check for ambiguous pronouns
        for token in doc:
            if token.pos_ == "PRON" and token.dep_ == "nsubj":
                suggestions.append({
                    "original": token.sent.text,
                    "suggestion": "Consider using a specific noun instead of pronoun",
                    "reason": "Ambiguous pronoun",
                    "pronoun": token.text
                })
        
        # Check for complex nested clauses
        for sent in doc.sents:
            clause_depth = self._calculate_clause_depth(sent)
            if clause_depth > 2:
                suggestions.append({
                    "original": sent.text,
                    "suggestion": "Consider simplifying nested clauses",
                    "reason": "Complex structure",
                    "depth": clause_depth
                })
        
        return suggestions
    
    def _analyze_technical_terms(self, doc) -> List[Dict]:
        """Analyze usage of technical terminology."""
        suggestions = []
        technical_terms = set()
        
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE"]:
                technical_terms.add(ent.text)
        
        # Check for undefined technical terms
        defined_terms = set()
        for sent in doc.sents:
            for term in technical_terms:
                if term in sent.text:
                    if term not in defined_terms:
                        suggestions.append({
                            "original": term,
                            "suggestion": f"Consider defining '{term}' on first use",
                            "reason": "Undefined technical term",
                            "context": sent.text
                        })
                    defined_terms.add(term)
        
        return suggestions
    
    def _analyze_consistency(self, doc) -> List[Dict]:
        """Analyze terminology and style consistency."""
        suggestions = []
        term_variants = defaultdict(set)
        
        # Track term variations
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"]:
                base = token.lemma_.lower()
                term_variants[base].add(token.text)
        
        # Check for inconsistent term usage
        for base, variants in term_variants.items():
            if len(variants) > 1:
                suggestions.append({
                    "original": list(variants),
                    "suggestion": f"Use consistent terminology for '{base}'",
                    "reason": "Inconsistent terms",
                    "variants": list(variants)
                })
        
        return suggestions
    
    def _generate_summary(self, content: str) -> str:
        """Generate a concise summary of the content."""
        try:
            summary = self.summarizer(content, max_length=130, min_length=30, do_sample=False)
            return summary[0]['summary_text']
        except Exception:
            # Fallback to first paragraph if summarization fails
            paragraphs = content.split('\n\n')
            return paragraphs[0] if paragraphs else content[:100] + "..."
    
    def _is_passive(self, sent) -> bool:
        """Check if a sentence is in passive voice."""
        return any(token.dep_ == "nsubjpass" for token in sent)
    
    def _calculate_clause_depth(self, sent) -> int:
        """Calculate the depth of nested clauses."""
        def get_depth(token):
            if not list(token.children):
                return 0
            return 1 + max(get_depth(child) for child in token.children)
        
        return get_depth(sent.root)
    
    def suggest_improvements(self, content: str) -> Dict:
        """Generate comprehensive improvement suggestions."""
        analysis = self.analyze_document(content)
        
        # Prioritize suggestions
        critical = []
        important = []
        minor = []
        
        # Process word choice suggestions
        for sugg in analysis["suggestions"]["word_choice"]:
            if sugg["reason"] == "Preferred term":
                minor.append(sugg)
            else:
                important.append(sugg)
        
        # Process sentence structure suggestions
        for sugg in analysis["suggestions"]["sentence_structure"]:
            if sugg.get("length", 0) > self.style_guide["sentence_length"]["max"] * 1.5:
                critical.append(sugg)
            else:
                important.append(sugg)
        
        # Process clarity suggestions
        for sugg in analysis["suggestions"]["clarity"]:
            if sugg.get("depth", 0) > 3:
                critical.append(sugg)
            else:
                important.append(sugg)
        
        # Process technical term suggestions
        for sugg in analysis["suggestions"]["technical_terms"]:
            important.append(sugg)
        
        # Process consistency suggestions
        for sugg in analysis["suggestions"]["consistency"]:
            minor.append(sugg)
        
        return {
            "summary": analysis["summary"],
            "metrics": analysis["metrics"],
            "suggestions": {
                "critical": critical,
                "important": important,
                "minor": minor
            },
            "readability_score": analysis["metrics"]["readability_score"],
            "improvement_count": len(critical) + len(important) + len(minor)
        }
    
    def rephrase_document(self, content: str) -> Tuple[str, Dict]:
        """Attempt to automatically improve document phrasing."""
        improvements = self.suggest_improvements(content)
        improved_content = content
        
        # Apply critical improvements first
        for sugg in improvements["suggestions"]["critical"]:
            if "original" in sugg and isinstance(sugg["original"], str):
                if "suggestion" in sugg and not sugg["suggestion"].startswith("Consider"):
                    improved_content = improved_content.replace(
                        sugg["original"],
                        sugg["suggestion"]
                    )
        
        # Apply important improvements
        for sugg in improvements["suggestions"]["important"]:
            if "original" in sugg and isinstance(sugg["original"], str):
                if "suggestion" in sugg and not sugg["suggestion"].startswith("Consider"):
                    improved_content = improved_content.replace(
                        sugg["original"],
                        sugg["suggestion"]
                    )
        
        # Apply minor improvements
        for sugg in improvements["suggestions"]["minor"]:
            if "original" in sugg and isinstance(sugg["original"], str):
                if "suggestion" in sugg and not sugg["suggestion"].startswith("Consider"):
                    improved_content = improved_content.replace(
                        sugg["original"],
                        sugg["suggestion"]
                    )
        
        # Calculate improvement metrics
        final_analysis = self.analyze_document(improved_content)
        
        return improved_content, {
            "original_metrics": improvements["metrics"],
            "improved_metrics": final_analysis["metrics"],
            "changes_made": len(improvements["suggestions"]["critical"]) +
                          len(improvements["suggestions"]["important"]) +
                          len(improvements["suggestions"]["minor"]),
            "readability_improvement": (
                final_analysis["metrics"]["readability_score"] -
                improvements["metrics"]["readability_score"]
            )
        }

def main():
    """Main function for CLI usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python docrephraser.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    rephraser = DocRephraser()
    improved_content, metrics = rephraser.rephrase_document(content)
    
    output_file = input_file.rsplit('.', 1)[0] + '_improved.' + input_file.rsplit('.', 1)[1]
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(improved_content)
    
    print(f"\nDocument Analysis Results:")
    print(f"- Changes made: {metrics['changes_made']}")
    print(f"- Readability improvement: {metrics['readability_improvement']:.2f} points")
    print(f"- Original readability score: {metrics['original_metrics']['readability_score']:.2f}")
    print(f"- Improved readability score: {metrics['improved_metrics']['readability_score']:.2f}")
    print(f"\nImproved document saved to: {output_file}")

if __name__ == "__main__":
    main()