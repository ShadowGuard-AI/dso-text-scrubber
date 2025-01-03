import argparse
import re
import sys
import logging
import chardet
from faker import Faker
from typing import List, Optional, Pattern, Callable, Any
import os


# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def detect_encoding(file_path: str) -> str:
    """Detects the encoding of a text file."""
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding']
            if encoding:
                return encoding
            else:
              return "utf-8"
    except Exception as e:
        logging.error(f"Error detecting encoding for {file_path}: {e}")
        return "utf-8"

def read_text_file(file_path: str) -> str:
    """Reads a text file and returns its content."""
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        sys.exit(1)

def write_text_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
    """Writes content to a text file."""
    try:
      with open(file_path, 'w', encoding=encoding) as f:
          f.write(content)
    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {e}")
        sys.exit(1)

def replace_match(match: re.Match, replacement: str) -> str:
    """Replaces a regex match with a specified string."""
    return replacement

def generate_fake_data(data_type: str) -> str:
  """Generate fake data based on the data type."""
  fake = Faker()
  if data_type == 'email':
      return fake.email()
  elif data_type == 'phone':
      return fake.phone_number()
  elif data_type == 'date':
      return fake.date()
  elif data_type == 'name':
      return fake.name()
  elif data_type == 'address':
      return fake.address()
  elif data_type == 'credit_card':
      return fake.credit_card_full()
  else:
    return fake.word() # Fallback to word if not recognized

def apply_regex_replacement(text: str, pattern: Pattern, replacement_func: Callable, **kwargs: Any) -> str:
  """Applies a regex pattern to replace content in the text, using a provided function."""
  try:
    return re.sub(pattern, lambda match: replacement_func(match, **kwargs), text)
  except Exception as e:
    logging.error(f"Error applying regex pattern {pattern}: {e}")
    return text # Return original text if error occurs


def sanitize_text(text: str, patterns: List[str], replacement_type: str, custom_replacement: Optional[str] = None) -> str:
    """Sanitizes the given text based on the provided patterns and replacement type."""
    
    sanitized_text = text
    
    if not patterns:
      logging.warning("No patterns provided for sanitization, returning original text.")
      return text

    for pattern_str in patterns:
        try:
            pattern = re.compile(pattern_str)
        except re.error as e:
            logging.error(f"Invalid regex pattern: {pattern_str} - {e}")
            continue # Skip invalid patterns

        if replacement_type == 'remove':
          sanitized_text = apply_regex_replacement(sanitized_text, pattern, replace_match, replacement="")
        elif replacement_type == 'fake':
          sanitized_text = apply_regex_replacement(sanitized_text, pattern, lambda match, data_type: generate_fake_data(data_type) ,data_type=pattern_str)
        elif replacement_type == 'custom':
          if not custom_replacement:
            logging.error("Custom replacement required but not provided for pattern: {pattern_str}")
            continue
          sanitized_text = apply_regex_replacement(sanitized_text, pattern, replace_match, replacement=custom_replacement)
        else:
            logging.error(f"Invalid replacement type: {replacement_type} - pattern: {pattern_str}")
    
    return sanitized_text

def setup_argparse() -> argparse.ArgumentParser:
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(description='Sanitize sensitive information from text files.')
    parser.add_argument('-i', '--input', type=str, help='Input file path, use - for stdin', default=None)
    parser.add_argument('-o', '--output', type=str, help='Output file path, use - for stdout', default=None)
    parser.add_argument('-p', '--patterns', type=str, nargs='+', help='Regex patterns for sensitive data.', default=[r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b',
            r'\d{3}-\d{3}-\d{4}', r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b']) # Default Patterns (email, phone, date, name)
    parser.add_argument('-r', '--replacement', type=str, choices=['remove', 'fake', 'custom'], default='remove', help='Replacement type (remove, fake, custom).')
    parser.add_argument('-c', '--custom-replacement', type=str, help='Custom replacement string if replacement type is "custom".')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    return parser

def main() -> None:
    """Main function to parse arguments, sanitize text, and handle I/O."""
    parser = setup_argparse()
    args = parser.parse_args()

    if args.input == '-':
        if sys.stdin.isatty():
          logging.error("No input provided via stdin.")
          sys.exit(1)
        text = sys.stdin.read()
    elif args.input:
        if not os.path.exists(args.input):
          logging.error(f"Input file does not exist: {args.input}")
          sys.exit(1)
        text = read_text_file(args.input)
    else:
        logging.error("Input is required either via --input or piped stdin.")
        sys.exit(1)


    sanitized_text = sanitize_text(text, args.patterns, args.replacement, args.custom_replacement)

    if args.output == '-':
        print(sanitized_text)
    elif args.output:
        write_text_file(args.output, sanitized_text)
    else:
        print(sanitized_text) # default to stdout if no output is specified

if __name__ == '__main__':
    main()