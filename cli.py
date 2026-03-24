import argparse
import sys
import os
import json
import docx
from pypdf import PdfReader
from core.analyzer import PlagiarismAnalyzer

# Initialize analyzer with the default JSON dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'documents.json')
analyzer = PlagiarismAnalyzer(DATA_PATH)

def extract_text(file_path):
    """Extract text from .txt, .pdf, or .docx files."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return None
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        elif ext == '.pdf':
            reader = PdfReader(file_path)
            content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext == '.docx':
            doc = docx.Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        else:
            print(f"Error: Unsupported file format '{ext}'")
            return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None
    
    return content

def run_analysis(input_val, is_file, analyzer, args):
    content = ""
    if not is_file:
        content = input_val
    else:
        content = extract_text(input_val)
        if content is None:
            return False

    if not content.strip():
        print("Error: Input content is empty.")
        return False

    # Run analysis
    results = analyzer.analyze(content)
    
    # Simple formatting of results
    print("\n" + "="*50)
    print(f"ANALYSIS REPORT: {input_val if is_file else 'Input Text'}")
    print(f"OVERALL PLAGIARISM: {results['overall_percentage']}%")
    print("="*50)
    
    if results['top_matches']:
        print("TOP SOURCE MATCHES:")
        for match in results['top_matches']:
            print(f" - {match['title']}: {round(match['score']*100, 2)}% similarity")
    else:
        print("No significant document matches found.")

    if results['plagiarized_sentences']:
        print(f"\n[!] Detected {len(results['plagiarized_sentences'])} matching sentences.")
        if args.verbose:
            for i, sent in enumerate(results['plagiarized_sentences']):
                print(f" {i+1}. Source: {sent['source']} ({round(sent['match_score']*100, 1)}%)")
                print(f"    Text: \"{sent['sentence']}\"")
    
    if args.save:
        with open(args.save, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"\n[+] Full report saved to {args.save}")
    
    return True

def main():
    import time
    parser = argparse.ArgumentParser(description="Plagiarism Analyzer CLI - Check for academic integrity in seconds.")
    
    # Input modes: --text, --file
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("-t", "--text", help="Text to analyze.")
    input_group.add_argument("-f", "--file", help="Path to a .txt, .pdf, or .docx file to analyze.")
    
    parser.add_argument("-v", "--verbose", action="store_true", help="Display all plagiarized sentences.")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold (0.0 to 1.0, default 0.7).")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch file for changes and re-analyze automatically.")

    args = parser.parse_args()

    if args.watch:
        if not args.file:
            print("Error: --watch requires a file (-f).")
            sys.exit(1)
        
        print(f"[*] Watching {args.file} for changes... (Ctrl+C to stop)")
        last_mtime = 0
        try:
            while True:
                current_mtime = os.path.getmtime(args.file)
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    print(f"\n[!] Change detected at {time.strftime('%H:%M:%S')}")
                    run_analysis(args.file, True, analyzer, args)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping watcher.")
    else:
        success = run_analysis(args.text if args.text else args.file, bool(args.file), analyzer, args)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
