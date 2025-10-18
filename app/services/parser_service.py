"""
Service layer for statement parser integration
Fully integrated bank statement parser - supports CSV, Excel, and PDF formats
"""
import csv
import pandas as pd
import logging
import fitz  # PyMuPDF
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO, BytesIO
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from enum import Enum

from app.schemas.schemas import TransactionCreate

logger = logging.getLogger(__name__)


# Entity classes for internal parser use
class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction:
    """Transaction entity for parser"""
    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str,
        transaction_date: date,
        balance_after: Decimal = None,
        reference_number: str = None
    ):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.description = description
        self.transaction_date = transaction_date
        self.balance_after = balance_after
        self.reference_number = reference_number


class StatementProcessingError(Exception):
    """Custom exception for statement processing errors"""
    pass


class StatementParser:
    """
    Parses bank statement files and converts them to Transaction entities.
    Supports CSV, Excel, and PDF formats with multiple bank support.
    """
    
    # Common column mappings for different banks
    COLUMN_MAPPINGS = {
        'default': {
            'date': ['date', 'transaction_date', 'trans_date', 'posting_date'],
            'description': ['description', 'desc', 'memo', 'details', 'transaction_details'],
            'amount': ['amount', 'amt', 'transaction_amount'],
            'debit': ['debit', 'debit_amount', 'withdrawal'],
            'credit': ['credit', 'credit_amount', 'deposit'],
            'balance': ['balance', 'running_balance', 'account_balance'],
            'reference': ['reference', 'ref', 'reference_number', 'transaction_id']
        },
        'chase': {
            'date': ['Transaction Date'],
            'description': ['Description'],
            'debit': ['Debit'],
            'credit': ['Credit'],
            'balance': ['Balance']
        },
        'bank_of_america': {
            'date': ['Date'],
            'description': ['Description'],
            'amount': ['Amount'],
            'balance': ['Running Bal.']
        },
        'wells_fargo': {
            'date': ['Date'],
            'amount': ['Amount'],
            'description': ['Description'],
            'balance': ['Balance']
        }
    }
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.pdf']
    
    async def parse_statement_file(
        self, 
        file_content: bytes, 
        filename: str,
        user_id: UUID,
        bank_name: Optional[str] = None
    ) -> List[Transaction]:
        """
        Parse a bank statement file and return transactions.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            user_id: User ID who uploaded the file
            bank_name: Optional bank name for format detection
            
        Returns:
            List[Transaction]
        """
        try:
            # Parse file content based on format
            if filename.lower().endswith('.csv'):
                transactions = await self._parse_csv_content(file_content, user_id, bank_name)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                transactions = await self._parse_excel_content(file_content, user_id, bank_name)
            elif filename.lower().endswith('.pdf'):
                transactions = await self._parse_pdf_content(file_content, user_id, bank_name)
            else:
                raise StatementProcessingError(f"Unsupported file format: {filename}")
            
            return transactions
        
        except Exception as e:
            logger.error(f"Error parsing statement file {filename}: {e}")
            raise StatementProcessingError(f"Failed to parse statement: {e}")

    async def _parse_pdf_content(
        self, 
        file_content: bytes, 
        user_id: UUID,
        bank_name: Optional[str] = None
    ) -> List[Transaction]:
        """Parse PDF file content into transactions."""
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            
            full_text = ""
            for page in doc:
                full_text += page.get_text("text")
            
            doc.close()

            # Determine which PDF parser to use
            if bank_name and bank_name.lower() in ['kaspi', 'kaspi_bank']:
                return self._parse_kaspi_pdf(full_text, user_id)
            else:
                if any(keyword in full_text.lower() for keyword in ['kaspi', 'каспи', 'kaspi bank']):
                    return self._parse_kaspi_pdf(full_text, user_id)
                else:
                    return self._parse_generic_pdf(full_text, user_id)
                    
        except Exception as e:
            raise StatementProcessingError(f"Error parsing PDF file: {e}")

    def _parse_kaspi_pdf(self, text: str, user_id: UUID) -> List[Transaction]:
        """Parse Kaspi Bank PDF statements."""
        transactions = []
        
        logger.info(f"PDF text preview (first 500 chars): {text[:500]}")
        
        # Look for transaction section markers
        transaction_markers = [
            "18.10.25\n- ",
            "17.10.25\n- ",
            "16.10.25\n- ",
            "15.10.25\n- ",
            "14.10.25\n- "
        ]
        
        search_start = -1
        for marker in transaction_markers:
            search_start = text.find(marker)
            if search_start != -1:
                logger.info(f"Found transaction section starting with: {marker}")
                break
        
        if search_start == -1:
            pattern_search = re.search(r"\d{2}\.\d{2}\.\d{2}\n[+\-]\s[\d\s,]+\s₸\n", text)
            if pattern_search:
                search_start = pattern_search.start()
                logger.info(f"Found transaction pattern at position: {search_start}")
            else:
                logger.warning("Could not find any transaction patterns in Kaspi PDF")
                return []

        search_text = text[search_start:]
        logger.info(f"Search text preview (800 chars): {search_text[:800]}")

        # Regex pattern to match transactions
        pattern = re.compile(
            r"(\d{2}\.\d{2}\.\d{2})\n"
            r"([+\-]\s[\d\s,]+\s₸)\n"
            r"([^\n]+)\n"
            r"([^\n\d]*?)(?=\n\d{2}\.\d{2}\.\d{2}|\n[A-ZА-Я]|$)",
            re.MULTILINE
        )

        matches_found = 0
        for match in pattern.finditer(search_text):
            matches_found += 1
            date_str, amount_str, operation, details = match.groups()
            
            date_str = date_str.strip()
            amount_str = amount_str.strip()
            operation = operation.strip()
            details = details.strip() if details else ""
            
            logger.info(f"Found transaction {matches_found}: date='{date_str}', amount='{amount_str}', operation='{operation}'")
            
            transaction_date = self._parse_date_kaspi(date_str)
            amount = self._parse_amount_kaspi(amount_str)

            if transaction_date is None or amount is None:
                logger.warning(f"Skipping transaction due to parsing error: date={date_str}, amount={amount_str}")
                continue

            transaction_type = TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE

            description = operation
            if details:
                description += f" - {details}"

            transactions.append(Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=transaction_date,
                amount=abs(amount),
                transaction_type=transaction_type,
                description=description
            ))

        logger.info(f"Parsed {len(transactions)} transactions from PDF")
        
        # Try simpler pattern if no transactions found
        if len(transactions) == 0:
            logger.info("Trying simpler parsing pattern...")
            simple_pattern = re.compile(
                r"(\d{2}\.\d{2}\.\d{2})\s*\n\s*([+\-]\s*[\d\s,]+\s*₸)",
                re.MULTILINE
            )
            
            for match in simple_pattern.finditer(search_text):
                date_str, amount_str = match.groups()
                logger.info(f"Simple pattern found: {date_str} - {amount_str}")
                
                transaction_date = self._parse_date_kaspi(date_str.strip())
                amount = self._parse_amount_kaspi(amount_str.strip())
                
                if transaction_date and amount is not None:
                    transaction_type = TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
                    
                    transactions.append(Transaction(
                        id=uuid4(),
                        user_id=user_id,
                        transaction_date=transaction_date,
                        amount=abs(amount),
                        transaction_type=transaction_type,
                        description="Transaction from PDF"
                    ))
            
            logger.info(f"Simple pattern parsed {len(transactions)} transactions")
        
        return transactions

    def _parse_generic_pdf(self, text: str, user_id: UUID) -> List[Transaction]:
        """Generic PDF parsing for other banks."""
        logger.warning("Generic PDF parsing not implemented yet")
        return []

    def _parse_date_kaspi(self, date_str: str) -> Optional[date]:
        """Parse Kaspi date format (dd.mm.yy)."""
        try:
            return datetime.strptime(date_str, "%d.%m.%y").date()
        except (ValueError, TypeError):
            logger.warning(f"Could not parse Kaspi date: {date_str}")
            return None

    def _parse_amount_kaspi(self, amount_str: str) -> Optional[Decimal]:
        """Parse Kaspi amount format (+ 5 953,33 ₸)."""
        if not amount_str:
            return None
        try:
            cleaned_str = amount_str.replace('₸', '').replace('T', '').replace(' ', '').replace(',', '.').strip()
            return Decimal(cleaned_str)
        except (InvalidOperation, TypeError):
            logger.warning(f"Could not parse Kaspi amount: {amount_str}")
            return None
    
    async def _parse_csv_content(
        self, 
        file_content: bytes, 
        user_id: UUID,
        bank_name: Optional[str] = None
    ) -> List[Transaction]:
        """Parse CSV file content into transactions."""
        try:
            content_str = file_content.decode('utf-8')
            
            for dialect in [csv.excel, csv.excel_tab]:
                try:
                    reader = csv.DictReader(StringIO(content_str), dialect=dialect)
                    rows = list(reader)
                    if rows:
                        break
                except:
                    continue
            else:
                df = pd.read_csv(StringIO(content_str))
                rows = df.to_dict('records')
            
            if not rows:
                raise StatementProcessingError("No data found in CSV file")
            
            column_mapping = self._detect_column_mapping(rows[0].keys(), bank_name)
            
            transactions = []
            for row in rows:
                try:
                    transaction = self._parse_transaction_row(row, column_mapping, user_id)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.warning(f"Skipping invalid transaction row: {e}")
                    continue
            
            return transactions
            
        except UnicodeDecodeError:
            raise StatementProcessingError("Unable to decode CSV file. Please ensure it's in UTF-8 format.")
        except Exception as e:
            raise StatementProcessingError(f"Error parsing CSV: {e}")
    
    async def _parse_excel_content(
        self, 
        file_content: bytes, 
        user_id: UUID,
        bank_name: Optional[str] = None
    ) -> List[Transaction]:
        """Parse Excel file content into transactions."""
        try:
            df = pd.read_excel(BytesIO(file_content))
            
            if df.empty:
                raise StatementProcessingError("No data found in Excel file")
            
            rows = df.to_dict('records')
            column_mapping = self._detect_column_mapping(df.columns, bank_name)
            
            transactions = []
            for row in rows:
                try:
                    transaction = self._parse_transaction_row(row, column_mapping, user_id)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.warning(f"Skipping invalid transaction row: {e}")
                    continue
            
            return transactions
            
        except Exception as e:
            raise StatementProcessingError(f"Error parsing Excel file: {e}")
    
    def _detect_column_mapping(self, columns: List[str], bank_name: Optional[str] = None) -> Dict[str, str]:
        """Detect which columns correspond to which transaction fields."""
        columns_lower = [col.lower().strip() for col in columns]
        
        bank_mappings = self.COLUMN_MAPPINGS.get(bank_name.lower() if bank_name else 'default', {})
        default_mappings = self.COLUMN_MAPPINGS['default']
        
        mapping = {}
        
        for field, possible_names in {**default_mappings, **bank_mappings}.items():
            for possible_name in possible_names:
                if possible_name.lower() in columns_lower:
                    original_col = columns[columns_lower.index(possible_name.lower())]
                    mapping[field] = original_col
                    break
        
        return mapping
    
    def _parse_transaction_row(
        self, 
        row: Dict[str, Any], 
        column_mapping: Dict[str, str],
        user_id: UUID
    ) -> Optional[Transaction]:
        """Parse a single row into a Transaction entity."""
        try:
            date_col = column_mapping.get('date')
            if not date_col or pd.isna(row.get(date_col)):
                return None
            
            transaction_date = self._parse_date(row[date_col])
            if not transaction_date:
                return None
            
            desc_col = column_mapping.get('description', '')
            description = str(row.get(desc_col, '')).strip()
            if not description:
                description = "Transaction"
            
            amount, transaction_type = self._extract_amount_and_type(row, column_mapping)
            if amount is None:
                return None
            
            balance = self._extract_balance(row, column_mapping)
            reference = self._extract_reference(row, column_mapping)
            
            return Transaction(
                id=uuid4(),
                user_id=user_id,
                amount=abs(amount),
                transaction_type=transaction_type,
                description=description,
                transaction_date=transaction_date,
                balance_after=balance,
                reference_number=reference
            )
            
        except Exception as e:
            logger.warning(f"Error parsing transaction row: {e}")
            return None
    
    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parse various date formats into a date object."""
        if pd.isna(date_value):
            return None
        
        try:
            if isinstance(date_value, datetime):
                return date_value.date()
            elif isinstance(date_value, date):
                return date_value
            
            date_str = str(date_value).strip()
            
            date_formats = [
                '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m/%d/%y', '%d/%m/%y',
                '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y', '%B %d, %Y', '%d %B %Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            parsed_date = pd.to_datetime(date_str, infer_datetime_format=True)
            return parsed_date.date()
            
        except Exception as e:
            logger.warning(f"Could not parse date '{date_value}': {e}")
            return None
    
    def _extract_amount_and_type(
        self, 
        row: Dict[str, Any], 
        column_mapping: Dict[str, str]
    ) -> Tuple[Optional[Decimal], Optional[TransactionType]]:
        """Extract amount and determine transaction type."""
        try:
            debit_col = column_mapping.get('debit')
            credit_col = column_mapping.get('credit')
            
            if debit_col and credit_col:
                debit_val = self._parse_amount(row.get(debit_col))
                credit_val = self._parse_amount(row.get(credit_col))
                
                if debit_val and debit_val > 0:
                    return Decimal(str(debit_val)), TransactionType.EXPENSE
                elif credit_val and credit_val > 0:
                    return Decimal(str(credit_val)), TransactionType.INCOME
            
            amount_col = column_mapping.get('amount')
            if amount_col:
                amount = self._parse_amount(row.get(amount_col))
                if amount is not None:
                    if amount >= 0:
                        return Decimal(str(amount)), TransactionType.INCOME
                    else:
                        return Decimal(str(abs(amount))), TransactionType.EXPENSE
            
            return None, None
            
        except Exception as e:
            logger.warning(f"Error extracting amount: {e}")
            return None, None
    
    def _parse_amount(self, amount_value: Any) -> Optional[float]:
        """Parse amount value from various formats."""
        if pd.isna(amount_value) or amount_value == '':
            return None
        
        try:
            amount_str = str(amount_value).strip()
            amount_str = amount_str.replace('$', '').replace('€', '').replace('£', '')
            amount_str = amount_str.replace(',', '').replace('(', '-').replace(')', '')
            amount_str = amount_str.strip()
            
            if not amount_str or amount_str == '-':
                return None
            
            return float(amount_str)
            
        except (ValueError, TypeError):
            return None
    
    def _extract_balance(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[Decimal]:
        """Extract account balance if available."""
        balance_col = column_mapping.get('balance')
        if balance_col:
            balance = self._parse_amount(row.get(balance_col))
            if balance is not None:
                return Decimal(str(balance))
        return None
    
    def _extract_reference(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[str]:
        """Extract reference number if available."""
        ref_col = column_mapping.get('reference')
        if ref_col:
            ref = row.get(ref_col)
            if ref and not pd.isna(ref):
                return str(ref).strip()
        return None


class ParserService:
    """
    Service class for bank statement parsing.
    Uses the integrated StatementParser.
    """
    
    def __init__(self):
        self.parser = StatementParser()
    
    async def parse_statement(self, file_content: bytes, filename: str, user_id: UUID) -> List[TransactionCreate]:
        """
        Parse bank statement and extract transactions.
        
        Args:
            file_content: The file content as bytes
            filename: Original filename (to determine format)
            user_id: User ID (UUID) for the transactions
        
        Returns:
            List of TransactionCreate objects
        """
        # Use the parser
        transactions = await self.parser.parse_statement_file(
            file_content=file_content,
            filename=filename,
            user_id=user_id,
            bank_name=None
        )
        
        # Convert Transaction entities to TransactionCreate schemas
        transaction_creates = []
        for t in transactions:
            # Store income as positive, expense as negative
            amount_value = float(t.amount) if t.transaction_type == TransactionType.INCOME else -float(t.amount)
            
            transaction_creates.append(
                TransactionCreate(
                    amount=amount_value,
                    description=t.description,
                    category=t.transaction_type.value,
                    transaction_date=datetime.combine(t.transaction_date, datetime.min.time())
                )
            )
        
        return transaction_creates


# Singleton instance
parser_service = ParserService()
