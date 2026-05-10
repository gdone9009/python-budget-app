import os
import argparse
from .repositories import CsvRepository
from .services import TransactionService, CategoryService, BudgetService

def initialize_system():
    """저장소 및 서비스 초기화"""
    data_dir = "./data"
    
    tx_repo = CsvRepository(os.path.join(data_dir, "transactions.csv"), ['id', 'type', 'date', 'amount', 'category', 'memo', 'tags'])
    cat_repo = CsvRepository(os.path.join(data_dir, "categories.csv"), ['name'])
    bud_repo = CsvRepository(os.path.join(data_dir, "budgets.csv"), ['month', 'amount'])
    
    return CategoryService(cat_repo, tx_repo), BudgetService(bud_repo), TransactionService(tx_repo, cat_repo), bud_repo

def handle_add_interactive(tx_service: TransactionService):
    print("--- 새로운 거래 내역을 추가합니다 ---")
    date = input("날짜(YYYY-MM-DD): ").strip()
    tx_type = input("타입(income/expense): ").strip()
    category = input("카테고리: ").strip()
    amount = input("금액(양수): ").strip()
    memo = input("메모(선택): ").strip()
    tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
    tx_service.add_transaction(tx_type, date, int(amount), category, memo, tags)

def main():
    cat_service, bud_service, tx_service, bud_repo = initialize_system()

    parser = argparse.ArgumentParser(description="파일 기반 가계부 콘솔 프로그램")
    subparsers = parser.add_subparsers(dest="command", help="사용할 명령어를 선택하세요")

    # 1. add 명령어
    subparsers.add_parser("add", help="대화형으로 거래를 추가합니다.")

    # 2. list 명령어
    parser_list = subparsers.add_parser("list", help="거래 목록을 조회합니다.")
    parser_list.add_argument("--limit", type=int, default=10, help="출력할 개수")

    # 3. summary 명령어
    parser_summary = subparsers.add_parser("summary", help="월별 요약 정보를 출력합니다.")
    parser_summary.add_argument("--month", required=True, help="조회할 월 (YYYY-MM)")
    parser_summary.add_argument("--top", type=int, default=3, help="지출 상위 N개")

    # 4. export 명령어
    parser_export = subparsers.add_parser("export", help="데이터를 CSV로 내보냅니다.")
    parser_export.add_argument("--out", required=True, help="저장할 파일명")
    parser_export.add_argument("--month", help="내보낼 월 (YYYY-MM)")

    args = parser.parse_args()

    if args.command == "add":
        handle_add_interactive(tx_service)
        
    elif args.command == "list":
        for tx in tx_service.list_transactions(args.limit):
            print(f"{tx['id']} | {tx['date']} | {tx['type']} | {tx['category']} | {tx['amount']} | {tx.get('memo','')}")
            
    elif args.command == "summary":
        result = tx_service.summarize_month(bud_repo, args.month, args.top)
        print(f"\n총 수입: {result['total_income']}원\n총 지출: {result['total_expense']}원\n잔액: {result['balance']}원")
        if result['warning']: print(result['warning'])
        print("--- 지출 TOP ---")
        for idx, (cat, amt) in enumerate(result['top_expenses'], 1):
            print(f"{idx}) {cat}: {amt}원")
            
    elif args.command == "export":
        tx_service.export_transactions(args.out, month=args.month)