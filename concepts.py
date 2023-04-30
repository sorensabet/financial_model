import loggingimport numpy as npimport pandas as pd import matplotlib.pyplot as plt class Earner:     def __init__(self,                  name: str,                  income_dict: dict,                 total_expenses: dict):        """            name: The name of the earner             income_dict: The projected monthly income of the earner over the length of the situation.                          A dictionary where the key is month number and the value is monthly income.         """                self.name=name        self.income=income_dict        self.debts = []        self.total_expenses = total_expenses        class Debt:    def __init__(self,                  earner: str,                  name: str,                  balance: float,                  limit: float,                  is_floating: False,                  apr: float,                  revolving=True,                  min_payment_flat_amount=50,                 min_payment_interest=False,                 min_payment_percent=0.02):                """            earner:                     The person whom the liability belongs to             name:                       The name of the liability            balance:                    The balance currently outstanding on the debt             limit:                      The total amount of credit available on the account             prime_rate:                 The prime rate portion of the account, as determined by the bank             is_floating:                True if the debt has floating interest, False otherwise            apr:                        The effective annual interest rate not including the prime rate, expressed as a float. Therefore, 22% is 0.22            revolving:                  Whether the source of credit is revolving or not.             min_payment_flat_amount:    The minimum amount that must be paid each month, regardless of the balance             min_payment_interest:       True if the interest charged to the card must be paid back in full each month.             min_payment_percent:        The percentage of the balance owing that must be paid each month. This can be zero if it is an interest-only payment credit product.                    """                    self.earner = earner        self.name = name         self.balance = balance         self.limit = limit         self.available_credit = limit - balance if revolving==True else 0        self.apr = apr        self.annual_interest = self.balance*(self.apr)        self.is_floating = is_floating         self.revolving=revolving         self.credit_utilization = 1 if self.limit==0 else self.balance/self.limit         self.min_payment_flat_amount = min_payment_flat_amount        self.min_payment_percent = min_payment_percent        self.min_payment_interest = min_payment_interest          self.minimum_payment = 0        # Okay. I have the basic information. Now what?         # I need to calculate the daily interest cost given this amount.        # I need a way to calculate 0% balance transfers and such             def info(self):         """            Print details about the debt         """                    print('Name', self.name)        print('Earner', self.earner)        print('Balance', self.balance)        print('Limit', self.limit)        print('Available credit', self.available_credit)        print('APR', self.apr)        print('Annual interest', self.annual_interest)        print('Is floating', self.is_floating)        print('Revolving', self.revolving)        print('Credit utilization', self.credit_utilization)        print('Minimum payment due', self.minimum_payment)        print('Minimum payment flat', self.minimum_payment_flat)        print('Minimum payment percent', self.minimum_payment_percent)                def compound(self):        """            Calculate the new balance after a compounding period             For simplicity, assume all rates are APR, and interest compounds once per month         """                # Approximate the new interest as         self.balance = self.balance + self.balance*(self.apr)/12          self.available_credit = self.limit - self.balance if self.revolving==True else 0        self.credit_utilization = 1 if self.limit==0 else self.balance/self.limit         self.annual_interest = self.balance*(self.apr)        return None        def calculate_minimum_payment(self):        """            Calculate the minimum payment due         """            # Generic repayment model         # Figure out the right question to ask here.         # How do I approximate the general repayment?         # Start with X% + interest         # Payment: Interest accumulated + X% of balance                                 rp_flat_fee = self.min_payment_flat_amount if self.balance > 0 else 0         rp_percent = (self.balance - self.annual_interest*31/365)*self.min_payment_percent if self.balance > 0 else 0         rp_monthly_interest = self.annual_interest*31/365 if self.min_payment_interest==True and self.balance > 0 else 0                 self.minimum_payment = rp_flat_fee + rp_percent + rp_monthly_interest                 if self.balance - self.minimum_payment < 0:             self.minimum_payment = self.balance                    return self.minimum_payment                             def payment(self, payment_amount):          """            Model a repayment to the credit source          """        # Account for edge case where payment_amount coming in is greater than the balance?         # Not in the debt object. Build this logic outside this object.                self.balance = self.balance - payment_amount         self.available_credit = self.limit - self.balance         self.credit_utilization = 1 if self.limit==0 else self.balance/self.limit         self.annual_interest = self.balance*(self.apr)        return None         def withdrawal(self, withdrawal_amount):         """            Withdrawing money from the credit source                 """                        available_amount = 0                if self.revolving==False:             raise Exception('Error - Tried to borrow from a non-revolving credit product')        elif withdrawal_amount <= self.available_credit:             self.balance += withdrawal_amount             self.available_credit = self.limit - self.balance             self.annual_interest = self.balance*(self.apr)            self.credit_utilization = 1 if self.limit==0 else self.balance/self.limit             available_amount = withdrawal_amount         elif withdrawal_amount > self.available_credit:                         available_amount = self.available_credit             self.balance += self.available_credit             self.available_credit = self.limit - self.balance            self.annual_interest = self.balance*(self.apr)            self.credit_utilization = 1 if self.limit==0 else self.balance/self.limit             assert('Tried to withdraw more than the available balance!')                return available_amount                         def credit_limit_change(self, change):         """            If change is >0, it represents a increase to the credit limit.             If change is <0, it represents a decrease in the available credit limit.         """            self.limit += change         self.credit_utilization = 1 if self.limit==0 else self.balance/self.limit         return None         def prime_rate_change(self, old_prime_rate, new_prime_rate):         """            Model changes to APR and annual interest because of changes in prime rate.             Assumes that the debt has floating interest rate.         """                prev_apr_non_prime_portion = self.apr - old_prime_rate        self.apr = new_prime_rate + prev_apr_non_prime_portion        self.annual_interest = self.balance*(self.apr)        return None     def interest_rate_change(self, apr, is_floating=True, revolving=True):        """            Model a change in interest rate not due to prime rate changes.                 Can be change in APR, change in floating/not-floating category, and change in revolving status        """                        self.apr = apr        self.annual_interest = self.balance*(self.apr)        self.is_floating=is_floating         self.revolving=revolving                                                