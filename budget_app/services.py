import re
import csv
from datetime import datetime
from collections import defaultdict
from typing import List, Generator, Dict, Any, Optional
from .repositories import CsvRepository
from .utils import handle_exceptions, BudgetError

class CategoryService:
    def __init__(self, category_repo: CsvRepository, tx_repo: CsvRepository):
        self.category_repo = category_repo
        self.tx_repo = tx_repo

    @handle_exceptions
    def add_category(self, name: str) -> None:
        if not name.strip():
            raise BudgetError("카테고리명이 비어있습니다.", "공백이 아닌 이름을 입력해 주세요.")
        for row in self.category_repo.read_all():
            if row['name'] == name:
                raise BudgetError(f"'{name}' 카테고리는 이미 존재합니다.", "다른 이름을 사용해 주세요.")
        self.category_repo.append_one({'name': name})
        print(f"[저장 완료] category={name}")

    @handle_exceptions
    def list_categories(self) -> List[str]:
        return [row['name'] for row in self.category_repo.read_all()]

    @handle_exceptions
    def remove_category(self, name: str) -> None:
        for tx in self.tx_repo.read_all():
            if tx.get('category') == name:
                raise BudgetError(
                    f"'{name}' 카테고리는 이미 사용 중이므로 삭제할 수 없습니다.", 
                    "해당 카테고리를 사용하는 거래 내역을 먼저 처리해 주세요."
                )
        
        def filter_out_category() -> Generator[Dict[str, Any], None, None]:
            found = False
            for row in self.category_repo.read_all():
                if row['name'] == name:
                    found = True
                    continue
                yield row
            if not found:
                raise BudgetError(f"'{name}' 카테고리를 찾을 수 없습니다.", "카테고리 목록을 확인해 주세요.")
                
        self.category_repo.rewrite_all(filter_out_category())
        print(f"[삭제 완료] category={name}")

class BudgetService:
    def __init__(self, budget_repo: CsvRepository):
        self.budget_repo = budget_repo

    @handle_exceptions
    def set_budget(self, month: str, amount: int) -> None:
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise BudgetError("날짜 형식이 올바르지 않습니다.", "예: 2024-01 형태로 입력해 주세요.")
        if int(amount) <= 0:
            raise BudgetError("예산은 양수여야 합니다.", "0보다 큰 금액을 입력해 주세요.")

        def update_or_append() -> Generator[Dict[str, Any], None, None]:
            updated = False
            for row in self.budget_repo.read_all():
                if row['month'] == month:
                    row['amount'] = amount
                    updated = True
                yield row
            if not updated:
                yield {'month': month, 'amount': amount}

        self.budget_repo.rewrite_all(update_or_append())
        print(f"[저장 완료] {month} 예산 {amount}원")

class TransactionService:
    def __init__(self, tx_repo: CsvRepository, category_repo: CsvRepository):
        self.tx_repo = tx_repo
        self.category_repo = category_repo

    @handle_exceptions
    def add_transaction(self, tx_type: str, date: str, amount: int, category: str, memo: str = "", tags: str = "") -> str:
        if tx_type not in ('income', 'expense'):
            raise BudgetError("타입이 올바르지 않습니다.", "'income' 또는 'expense'를 입력하세요.")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            raise BudgetError("날짜 형식이 올바르지 않습니다.", "예: 2024-01-15 형식으로 입력해 주세요.")
        if int(amount) <= 0:
            raise BudgetError("금액은 양수여야 합니다.", "0보다 큰 정수를 입력해 주세요.")

        valid_categories = [row['name'] for row in self.category_repo.read_all()]
        if category not in valid_categories:
            raise BudgetError(f"'{category}' 카테고리가 존재하지 않습니다.", "먼저 카테고리를 등록해 주세요.")

        tx_id = f"TX-{int(datetime.now().timestamp())}"
        data = {'id': tx_id, 'type': tx_type, 'date': date, 'amount': amount, 'category': category, 'memo': memo, 'tags': tags}
        self.tx_repo.append_one(data)
        print(f"[저장 완료] id={tx_id}")
        return tx_id

    @handle_exceptions
    def list_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        txs = list(self.tx_repo.read_all())
        txs.sort(key=lambda x: x['date'], reverse=True)
        return txs[:limit]

    @handle_exceptions
    def search_transactions(self, from_date: str = None, to_date: str = None, category: str = None, tx_type: str = None, q: str = None, tag: str = None) -> Generator[Dict[str, Any], None, None]:
        for row in self.tx_repo.read_all():
            if from_date and row['date'] < from_date: continue
            if to_date and row['date'] > to_date: continue
            if category and row['category'] != category: continue
            if tx_type and row['type'] != tx_type: continue
            if q and (not row.get('memo') or q.lower() not in row['memo'].lower()): continue
            if tag and (not row.get('tags') or tag not in row['tags']): continue
            yield row

    @handle_exceptions
    def summarize_month(self, budget_repo: CsvRepository, month: str, top_n: int = 3) -> Dict[str, Any]:
        total_income = 0
        total_expense = 0
        category_expense = defaultdict(int)

        for row in self.tx_repo.read_all():
            if row['date'].startswith(month):
                amount = int(row['amount'])
                if row['type'] == 'income': total_income += amount
                elif row['type'] == 'expense': 
                    total_expense += amount
                    category_expense[row['category']] += amount

        top_expenses = sorted(category_expense.items(), key=lambda x: x[6], reverse=True)[:top_n]

        budget_amount = None
        for b_row in budget_repo.read_all():
            if b_row['month'] == month:
                budget_amount = int(b_row['amount'])
                break
        
        warning_msg = None
        if budget_amount:
            usage_rate = (total_expense / budget_amount) * 100
            if usage_rate > 100:
                warning_msg = f"[경고] 예산을 {usage_rate - 100:.1f}% 초과했습니다!"

        return {"month": month, "total_income": total_income, "total_expense": total_expense, "balance": total_income - total_expense, "top_expenses": top_expenses, "budget": budget_amount, "warning": warning_msg}

    @handle_exceptions
    def export_transactions(self, out_path: str, month: str = None, from_date: str = None, to_date: str = None) -> None:
        if month: from_date, to_date = f"{month}-01", f"{month}-31"
        generator = self.search_transactions(from_date=from_date, to_date=to_date)
        fieldnames = ['date', 'type', 'category', 'amount', 'memo', 'tags']
        count = 0
        
        with open(out_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for row in generator:
                if isinstance(row.get('tags'), list): row['tags'] = ",".join(row['tags'])
                writer.writerow(row)
                count += 1
        print(f"[완료] {out_path} ({count} records)")

    @handle_exceptions
    def import_transactions(self, in_path: str) -> None:
        count = 0
        with open(in_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.add_transaction(row['type'], row['date'], int(row['amount']), row['category'], row.get('memo', ''), row.get('tags', ''))
                count += 1
        print(f"[완료] imported={count}, skipped=0")