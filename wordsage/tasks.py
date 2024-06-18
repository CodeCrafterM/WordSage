# wordsage/tasks.py

"""
Tasks for WordSage.
"""

import os
from collections import Counter
from typing import Dict
from wordsage.celery_app import app

@app.task
def reverse_string(my_string: str):
    """Reverse a given string."""
    return my_string[::-1]

@app.task
def process_text_files(folder_path: str, num_files: int = 4) -> Dict[str, int]:
    """Process text files in the given folder and return the most common words."""
    try:
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")

        # Collect all text files from the directory and its subdirectories
        files = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if filename.endswith('.txt'):
                    files.append(os.path.join(root, filename))

        if len(files) < num_files:
            raise ValueError(
                f"Not enough text files in the folder. Found {len(files)}, required {num_files}."
            )

        files = files[:num_files]
        word_counter: Counter = Counter()

        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    words = line.split()
                    word_counter.update(words)

        most_common_words: Dict[str, int] = dict(word_counter.most_common(10))
        return most_common_words

    except FileNotFoundError as fnf_error:
        return {"error": str(fnf_error)}
    except ValueError as val_error:
        return {"error": str(val_error)}
    except Exception as gen_error:
        return {"error": str(gen_error)}

@app.task
def process_text_files_v2(folder_path: str, num_files: int = 4) -> Dict[str, int]:
    """Process text files in the given folder and return the most common words (version 2)."""
    """This version uses a nested loop to manually count the occurrences of each word. This is less efficient compared to using the Counter class in v1."""
    try:
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")

        # Collect all text files from the directory and its subdirectories
        files = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if filename.endswith('.txt'):
                    files.append(os.path.join(root, filename))

        if len(files) < num_files:
            raise ValueError(
                f"Not enough text files in the folder. Found {len(files)}, required {num_files}."
            )

        files = files[:num_files]
        word_count: Dict[str, int] = {}

        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    words = line.lower().split()  # Convert words to lowercase
                    words = [word.strip('.,!?;()[]') for word in words]  # Strip punctuation

                    for word in words:
                        if word in word_count:
                            word_count[word] += 1
                        else:
                            word_count[word] = 1

        # Sort the dictionary by value and take the top 10 items
        most_common_words = dict(sorted(word_count.items(), key=lambda item: item[1], reverse=True)[:10])
        return most_common_words

    except FileNotFoundError as fnf_error:
        return {"error": str(fnf_error)}
    except ValueError as val_error:
        return {"error": str(val_error)}
    except Exception as gen_error:
        return {"error": str(gen_error)}