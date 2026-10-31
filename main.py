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


DEFAULT_PATTERN_TYPES = {}

def sanitize_text(text: str, patterns: List[str], replacement_type: str, custom_replacement: Optional[str] = None, pattern_types: Optional[dict] = None):
    """Sanitizes text. Returns (sanitized_text, match_count). Patterns are compiled
    by the caller at startup; an invalid pattern fails the run before this is called."""
    if replacement_type == 'custom' and not custom_replacement:
        logging.error(f"Custom replacement required but not provided for pattern: {patterns[0] if patterns else ''}")
        sys.exit(1)
    sanitized_text = text
    total = 0
    types_map = pattern_types or {}
    for pattern_str in patterns:
        pattern = re.compile(pattern_str)
        count = len(pattern.findall(sanitized_text))
        total += count
        if count == 0:
            continue
        data_type = types_map.get(pattern_str, 'word')
        if replacement_type == 'remove':
          sanitized_text = apply_regex_replacement(sanitized_text, pattern, replace_match, replacement="")
        elif replacement_type == 'fake':
          sanitized_text = apply_regex_replacement(sanitized_text, pattern, lambda match, data_type=data_type: generate_fake_data(data_type))
        elif replacement_type == 'custom':
          sanitized_text = apply_regex_replacement(sanitized_text, pattern, replace_match, replacement=custom_replacement)
        else:
            logging.error(f"Invalid replacement type: {replacement_type} - pattern: {pattern_str}")
            sys.exit(1)
    return sanitized_text, total

def setup_argparse() -> argparse.ArgumentParser:
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(description='Sanitize sensitive information from text files.')
    parser.add_argument('-i', '--input', type=str, help='Input file path, use - for stdin', default=None)
    parser.add_argument('-o', '--output', type=str, help='Output file path, use - for stdout', default=None)
    _name_pat = r'\b(?!(?:The|A|An|This|That|These|Those|My|His|Her|Their|Our|Your)\s)[A-Z][a-z]+\s[A-Z][a-z]+\b'
    _defaults = [r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b',
            r'\d{3}-\d{3}-\d{4}', r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', _name_pat]
    _types = {_defaults[0]: 'email', _defaults[1]: 'phone', _defaults[2]: 'date', _defaults[3]: 'name'}
    parser.add_argument('-p', '--patterns', type=str, nargs='+', help='Regex patterns for sensitive data.', default=_defaults)
    parser.set_defaults(_pattern_types=_types)
    parser.add_argument('-r', '--replacement', type=str, choices=['remove', 'fake', 'custom'], default='remove', help='Replacement type (remove, fake, custom).')
    parser.add_argument('-c', '--custom-replacement', type=str, help='Custom replacement string if replacement type is "custom".')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    return parser

def main() -> None:
    """Main function to parse arguments, sanitize text, and handle I/O."""
    parser = setup_argparse()
    args = parser.parse_args()

    # Custom mode requires a replacement string.
    if args.replacement == 'custom' and not args.custom_replacement:
        logging.error(f"Custom replacement required but not provided for pattern: {args.patterns[0] if args.patterns else ''}")
        sys.exit(1)
    # Compile every pattern at startup; any failure exits before output is opened.
    for _pat in (args.patterns or []):
        try:
            re.compile(_pat)
        except re.error as e:
            logging.error(f"Invalid regex pattern: {_pat} - {e}")
            sys.exit(1)
    if not args.patterns:
        print("No patterns provided. Nothing scrubbed.")
        sys.exit(1)
    # Same-path guard: resolved output must not equal the input file.
    if args.input and args.input != '-' and args.output and args.output != '-':
        try:
            if os.path.realpath(args.input) == os.path.realpath(args.output) or os.path.abspath(args.input) == os.path.abspath(args.output):
                logging.error("Output path resolves to the input file. Refusing to overwrite the input.")
                sys.exit(1)
            # realpath resolves symlinks and ./ aliases; also compare resolved Paths
            from pathlib import Path as _P
            if _P(args.input).resolve() == _P(args.output).resolve():
                logging.error("Output path resolves to the input file. Refusing to overwrite the input.")
                sys.exit(1)
        except SystemExit:
            raise
        except Exception:
            pass

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


    _known_types = {
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b': 'email',
        r'\d{3}-\d{3}-\d{4}': 'phone',
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}': 'date',
    }
    for _k, _v in list(_known_types.items()):
        pass
    # name pattern is the remaining default pattern (the guarded Title Case pair)
    _pattern_types = dict(_known_types)
    for _pat in args.patterns:
        if _pat not in _pattern_types:
            _pattern_types[_pat] = 'name' if ('[A-Z]' in _pat and '[a-z]' in _pat) else 'word'
    sanitized_text, match_count = sanitize_text(text, args.patterns, args.replacement, args.custom_replacement, pattern_types=_pattern_types)
    logging.info(f"Scrubbed {match_count} value(s).")
    if match_count == 0:
        print("No values scrubbed.")
        sys.exit(1)

    if args.output == '-':
        print(sanitized_text)
    elif args.output:
        write_text_file(args.output, sanitized_text)
    else:
        print(sanitized_text) # default to stdout if no output is specified

if __name__ == '__main__':
    main()