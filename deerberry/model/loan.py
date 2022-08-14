from decimal import Decimal
from typing import Literal

from pydantic import BaseModel
import datetime as dt


class LoanDetails(BaseModel):
    loanId: str
    countryId: int
    countryIso: str
    loanOrignator: str
    originatorId: int
    issuedDate: dt.date
    finalPaymentDate: dt.date
    termType: str | Literal['BUSINESS']
    status: str
    interestRate: Decimal
    loanAmount: Decimal
    assignedAmount: Decimal
    availableToInvest: Decimal
    minimumInvestmentAmount: Decimal
    investedAmount: Decimal
    currencySign: str
    buyback: bool
    sellback: bool
    days: int
    order_position: int


# TODO
class Originator(BaseModel): pass


# TODO
class Borrower(BaseModel): pass


# TODO
class Schedule(BaseModel): pass


# TODO
class Pledge(BaseModel): pass


class Loan(BaseModel):
    loan: LoanDetails
    originator: Originator
    borrower: Borrower
    schedule: Schedule
    pledge: Pledge
