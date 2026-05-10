import csv
import os
from typing import Generator, List, Dict, Any

class CsvRepository:
    def __init__(self, filepath: str, fieldnames: List[str]):
        self.filepath = filepath
        self.fieldnames = fieldnames
        
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def read_all(self) -> Generator[Dict[str, str], None, None]:
        with open(self.filepath, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    def append_one(self, data: Dict[str, Any]) -> None:
        with open(self.filepath, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(data)

    def rewrite_all(self, data_iterator: Generator[Dict[str, Any], None, None]) -> None:
        temp_filepath = f"{self.filepath}.temp"
        try:
            with open(temp_filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                for row in data_iterator:
                    writer.writerow(row)
            os.replace(temp_filepath, self.filepath)
        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise e