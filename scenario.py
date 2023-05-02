import os import logging  import numpy as npimport pandas as pdimport datetime as dateimport matplotlib.pyplot as plt from concepts import Debt, Earner# Delete log file if it exists if os.path.exists('log.txt'):    os.remove('log.txt')# Set up logging. logger = logging.getLogger('')logger.setLevel(logging.DEBUG)logger.handlers.clear()ch = logging.StreamHandler()ch.setLevel(logging.DEBUG)# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')formatter = logging.Formatter('%(message)s')ch.setFormatter(formatter)fh = logging.FileHandler('log.txt')fh.setLevel(logging.DEBUG)logger.addHandler(ch)logger.addHandler(fh) # Set the number of months to run the simulation. num_months = 10expense_monthly_inflation_rate = 0.005# Okay. Step 1. Model the growth of a test debt that I have, using easily verifiable numbers, to ensure that things are working correctly. def describe_debts(debts):         sorted_debts = sorted([debt for debt in debts.values()],                                              key=lambda x: x.apr, reverse=True)        active_debts = [debt for debt in sorted_debts if debt.balance>0]    cleared_debts = [debt for debt in sorted_debts if debt.balance==0]        # active_debts = {x: y for x,y in debts.items() if y.balance > 0}    # cleared_debts = {x: y for x,y in debts.items() if y.balance == 0}        if len(active_debts) > 0:        logger.debug('\n\tActive Debt Status:')        # for _, debt in active_debts.items():         for debt in active_debts:            logger.debug('\t\t%s %15s: $%9.2f of $%10.2f - Costing $%8.2f/year ' % (debt.earner, debt.name, debt.balance, debt.limit, debt.annual_interest))    if len(cleared_debts) > 0:        logger.debug('\n\tCleared Debt Status:')        # for _, debt in cleared_debts.items():         for debt in cleared_debts:            logger.debug('\t\t%s %15s: $%9.2f available' % (debt.earner, debt.name, debt.available_credit))                return None def get_current_state(debts):         cs = {        'total_debt': 0,         'total_limit': 0,         'total_revolving_limit': 0,        'total_available_credit': 0,         'total_annual_interest_due': 0,         'total_credit_utilization': 0}        for _, debt in debts.items():         cs['total_debt'] += debt.balance          cs['total_limit'] += debt.limit        cs['total_revolving_limit'] += debt.limit if debt.is_revolving==True else debt.balance        cs['total_available_credit'] += debt.available_credit         cs['total_annual_interest_due'] += debt.annual_interest     cs['total_credit_utilization'] = cs['total_debt']/cs['total_revolving_limit']    return cs def load_data(        earn_path='/Users/soren/Desktop/financial_model/data/incomes.csv',        expense_path='/Users/soren/Desktop/financial_model/data/expenses.csv',        debt_path='/Users/soren/Desktop/financial_model/data/debts.csv',         interest_changes_path='/Users/soren/Desktop/financial_model/data/interest_rate_changes.csv',        prime_rate_changes_path='/Users/soren/Desktop/financial_model/data/prime_rate_changes.csv',        num_months=120):    ### STEP 0. Ingest all data    earners = {}    incomes = pd.read_csv(earn_path)    expenses = pd.read_csv(expense_path)    pr_dict = pd.read_csv(prime_rate_changes_path, index_col='month')['rate'].to_dict()    logger.debug('Ingesting earner monthly incomes from path: %s' % (earn_path))    logger.debug('Ingesting earner expenses from path: %s' % (earn_path))    logger.debug('Ingesting prime rates from %s' % (prime_rate_changes_path))    logger.debug('Identified earners: %s:' % (incomes['earner'].unique()))    # Step 1. Extract monthly income changes and store in income earner dictionary        earner_income_dict = {}    for earner in incomes['earner'].unique():         logger.debug('\nEarner: %s' % earner)        logger.debug('\tAssembling monthly incomes')        earner_income_df = incomes.loc[incomes['earner'] == earner][['month', 'after_tax_income']]        earner_income_df.index = earner_income_df.month         earner_income_dict[earner] = earner_income_df[['after_tax_income']].to_dict()['after_tax_income']                    earner_monthly_expenses = expenses.loc[expenses['earner'] == earner]['amount'].sum()        logger.debug('\tCalculating total monthly expenses at: $%0.2f' % (earner_monthly_expenses))                monthly_income = 0        for m in range(0, num_months):             if m in earner_income_dict[earner].keys():                monthly_income = earner_income_dict[earner][m]            else:                 earner_income_dict[earner][m] = monthly_income             earners[earner] = Earner(earner, earner_income_dict[earner], total_expenses=earner_monthly_expenses)                    # Step 2. Create monthly lookup table for prime rate    monthly_pr = pr_dict[0]    for m in range(0,num_months):        if m in pr_dict.keys():             monthly_pr = pr_dict[m]        else:             pr_dict[m] = monthly_pr             # Step 2b. Ingest debt and interest rate change data.    debts = {y['name']: Debt(**y) for x, y in pd.read_csv(debt_path).to_dict(orient='index').items()}    irc_df = pd.read_csv(interest_changes_path)        # Step 2c. Set starting APR for each debt in interest rate change lookup table     irc_dict = {earner: {} for earner in earners.keys()}    for _, d in debts.items():         irc_dict[d.earner][d.name] = {0: d.apr}        # If there are no rate changes, just assign the interest rate from the first month    # Earner         # Debt             # Interest rates                for earner in irc_df['earner'].unique():         earner_irc_df = irc_df.loc[irc_df['earner'] == earner]                for debt_name in earner_irc_df['name'].unique():                         debt_irc_df = earner_irc_df.loc[earner_irc_df['name'] == debt_name]            debt_irc_df.index = debt_irc_df['month']                        if len(debt_irc_df) > 0:                irc_dict[earner][debt_name] = debt_irc_df[['apr', 'is_revolving', 'is_floating']].to_dict(orient='index')                                        # Step 2c. Assign debts to earners    for _, debt in debts.items():         earners[debt.earner].debts.append(debt)        logger.debug('\tAssigned debt %s to %s' % (debt.name, earners[debt.earner].name))    return earners, debts, pr_dict, irc_dictdef borrow_from_lowest_interest_product(amount, debts):     """        amount: The amount to try to borrow         debts:  The credit products available                 Returns: The amount that was successfully borrowed from the available credit     """        # Steps     # 1. Identify debts in order of lowest interest, that have credit available     # 2. Withdraw from the lowest interest product that offers revolving credit until the amount required has been withdrawn.         lowest_interest_revolving_debts = sorted([debt for debt in debts.values() if debt.is_revolving==True],                                              key=lambda x: x.apr)        amount_withdrawn = 0        # I need logic to split the amount I wish to withdraw among the available sources of credit     for debt in lowest_interest_revolving_debts:         if debt.available_credit - amount >= 0:             debt.withdrawal(amount)            amount_withdrawn = amount             break         else:             amount_withdrawn += debt.available_credit             debt.withdrawal(debt.available_credit)        return amount_withdrawn def apply_remaining_cash_highest_interest_debts(cash_available, debts):    """        cash_available: A float representing how much money is left after all minimum payments have been made         debts:          A dictionary of debt objects.    """        # Logic. Apply the remaining payment to the highest interest debt.     # In the edge case where the balance on the highest interest debt is less than the remaining cash, pay off the highest interest_debt and apply remaining cash to the next remaining debt.     logger.debug('Directing remaining cash towards highest interest debts')    highest_interest_debts = sorted([debt for debt in debts.values() if debt.balance > 0], key=lambda x: x.apr, reverse=True)    debt_idx = 0            # Okay. What do I log here?     # Try to apply excess cash towards all remaining revolving sources of credit.     # Save anything that remains.         counter = 0    while cash_available > 0 and debt_idx < len(highest_interest_debts):                     # If all the cash will go towards one balance         if highest_interest_debts[debt_idx].balance >= cash_available and highest_interest_debts[debt_idx].is_revolving==True:             highest_interest_debts[debt_idx].payment(cash_available)            logger.debug('\tUsed all remaining cash to make payment of $%0.2f towards %s' % (cash_available, highest_interest_debts[debt_idx].name))            cash_available -= cash_available                        elif highest_interest_debts[debt_idx].is_revolving==True:            # If we can completely pay off the highest interest debt and have leftover cash                                     payment_to_current_debt = highest_interest_debts[debt_idx].balance             cash_available -= payment_to_current_debt            highest_interest_debts[debt_idx].payment(payment_to_current_debt)            logger.debug('\tUsed $%0.2f to pay off %s, with $%0.2f remaining' % (payment_to_current_debt, highest_interest_debts[debt_idx].name, cash_available))            debt_idx += 1             # Okay. my logic to calculate the payment to the current debt is incorrect...             # I need more robust logic to account for when cash can be less or more than         else:             debt_idx += 1        counter += 1        return cash_available def optimize_debt_allocations(earners, debts, max_utilization=0.85):    """        Reshuffle debts b/w available credit products to optimize situation.         The two optimizing strategiees are optimizing for interest or optimizing for cash flow.             Optimizing for interest will re-allocate total debts to the lowest revolving interest products while respecting the max_utilization limit (per product)            Optimizing for cash flow will re-allocate total debts across revolving credit products to achieve minimum monthly payments                    debts:              The dictionary of all debts         max_utilization:    The max credit utilization available for reshuffling from revolving credit products.            """        logger.debug('\nNow attempting to optimize debt allocation among revolving credit products, borrowing up to %0.2f%%' % (100*max_utilization))    debt_change_dict = {e: {} for e, _ in earners.items()}    revolving_debts = {debt_name: debt for debt_name, debt in debts.items() if debt.is_revolving}                # First pass: Identify how much we can withdraw from each revolving credit product.    reallocation_amount = 0    prior_annual_cost = sum(debt.annual_interest for debt in debts.values())            for _, debt in revolving_debts.items():         debt_change_dict[debt.earner][debt.name] = max(debt.limit*max_utilization - debt.balance,0)        prior_annual_cost += debt.annual_interest                 logger.debug('\tDebt: %s\'s %10s, balance:$%8.2f, limit: $%8.2f, Will borrow: $%0.2f' % (debt.earner, debt.name, debt.balance, debt.limit, max(debt.limit*max_utilization - debt.balance,0)))        reallocation_amount += debt.withdrawal(max(debt.limit*max_utilization - debt.balance,0))                # Second pass: Go in descending order of interest rate, and apply payments from highest to lowest interest     highest_interest_revolving_debts = sorted([debt for debt in revolving_debts.values()],                                              key=lambda x: x.apr, reverse=True)        logger.debug('\nTotal amount withdrawn from revolving credit product: $%0.2f\n' % (reallocation_amount))        for debt in highest_interest_revolving_debts:                 if reallocation_amount > 0 and debt.balance - reallocation_amount > 0:             debt_change_dict[debt.earner][debt.name] -= reallocation_amount             debt.payment(reallocation_amount)            logger.debug('\tUsed all remaining $%0.2f to pay %s\'s %s\n' % (reallocation_amount, debt.earner, debt.name))            reallocation_amount -= reallocation_amount             break                 elif reallocation_amount > 0 and debt.balance - reallocation_amount < 0:             payment_amount = debt.balance             debt_change_dict[debt.earner][debt.name] -= payment_amount             reallocation_amount -= payment_amount             debt.payment(payment_amount)            logger.debug('\tReallocated $%0.2f to pay %s\'s %s' % (payment_amount, debt.earner, debt.name))    # Log net changes to each revolving product.     logger.debug('\nNet changes to credit products')    for _, debt in revolving_debts.items():         if debt_change_dict[debt.earner][debt.name] > 0:                 logger.debug('\t%s\'s %s: Withdrew $%0.2f' % (debt.earner, debt.name, debt_change_dict[debt.earner][debt.name]))        elif debt_change_dict[debt.earner][debt.name] < 0:             logger.debug('\t%s\'s %s: Paid $%0.2f' % (debt.earner, debt.name, abs(debt_change_dict[debt.earner][debt.name])))    # Recalculate total annual cost     new_annual_cost = sum(debt.annual_interest for debt in debts.values())    logger.debug('\nFinished reallocating debts, saving $%0.2f in annual interest!' % (prior_annual_cost - new_annual_cost))     logger.debug('Reallocation amount remaining: $%0.2f' % reallocation_amount)        return None     if __name__ == '__main__':         results = []    logger.debug('Running simulation for %d months.' % (num_months))    earners, debts, prime_rate_lookup, irc_lookup = load_data()        optimize_debt_allocations(earners, debts, max_utilization=0.95)        total_savings = 0        for m in range(0, num_months):                 ms = {'month': m,             'total_debt': 0,             'total_limit': 0,             'total_available_credit': 0,             'total_revolving_limit': 0,             'total_annual_interest_due': 0,             'total_min_payments': 0,             'total_shortfall': 0}                logger.debug('\n\n\n\n***************************\n* NOW SIMULATING MONTH: %d *\n***************************\n' % (m))        # CALCULATE MONTHLY INCOMES        logger.debug('\nSumming total monthly income from all earners...')                # Calculate total cash and contribution by earner        total_cash_available = total_savings         total_savings = 0                 logger.debug('Total savings from prev months:   $%0.2f' % (total_cash_available))        for _, e in earners.items():             earner_contribution = e.income[m] - e.total_expenses*(1 + expense_monthly_inflation_rate)**m            if earner_contribution > 0:                 logger.debug('%7s contributed after expenses:       $%10.2f' % (e.name, earner_contribution))            elif earner_contribution < 0:                logger.debug('\t%7s amount required to meet expenses: $%10.2f' % (e.name, earner_contribution))            total_cash_available += earner_contribution                logger.debug('-------------------------------------------------------')        if total_cash_available >= 0:             logger.debug('Total cash available for month %d:           $%10.2f' % (m, total_cash_available))        else:             logger.debug('Require an additional $%10.2f to meet monthly expenses' % (abs(total_cash_available)))            logger.debug('\tAttempting to withdraw required amount from revolving credit products')            total_cash_available += borrow_from_lowest_interest_product(abs(total_cash_available), debts)                                    if total_cash_available == 0:                logger.debug('\tSuccessfully withdrew required shortfall from credit products')            elif total_cash_available < 0:                 raise Exception('NOT ENOUGH CREDIT AVAILABLE TO MEET MINIMUM MONTHLY EXPENSES - GAME OVER')          # CHECK FOR CHANGES IN PRIME RATE         if m > 0 and prime_rate_lookup[m] != prime_rate_lookup[m-1]:             logger.debug('\nNew prime rate is %0.2f%%' % (100*prime_rate_lookup[m]))            logger.debug('Updating floating debts with new prime rates')                        for _, debt in debts.items():                if debt.is_floating:                     debt.prime_rate_change(prime_rate_lookup[m-1], prime_rate_lookup[m])                    logger.debug('\t%s\'s %s - APR: %5.2f%%, Annual cost: $%0.2f' % (debt.earner, debt.name, 100*debt.apr, debt.annual_interest))        # CHECK FOR OTHER CHANGES IN APR, FLOATING STATUS, OR REVOLVING STATUS            logger.debug('\n\nCheck for changes in APR, floating, or revolving status')                for debt_name, debt in debts.items():             # Check for changes in interest rates this month             if m > 0 and m in irc_lookup[debt.earner][debt_name]:                d = irc_lookup[debt.earner][debt_name][m]                debt.interest_rate_change(**d)                logger.debug('\tInterest rate changed for %s:     APR: %0.2f%%, floating:%s, revolving:%s' % (debt_name, d['apr']*100, d['is_floating'], d['is_revolving']))                    # COMPOUND DEBTS        logger.debug('\n\nCompounding all outstanding debts\n---------------------')                        for debt_name, debt in debts.items():                         debt.compound()            debt.calculate_minimum_payment()            ms['total_limit'] += debt.limit             ms['total_debt'] += debt.balance            ms['total_min_payments'] += debt.minimum_payment            ms['total_revolving_limit'] += debt.limit if debt.is_revolving==True else debt.balance            ms['total_available_credit'] += debt.available_credit            ms['total_annual_interest_due'] += debt.annual_interest            if debt.balance > 0:                 logger.debug('\tCompounded %10s - New Balance: $%6.2f\tAPR: %0.2f%%\tAnnual Cost: $%6.2f\t Min Payment: $%6.2f' % (debt.name, debt.balance, debt.apr*100, debt.annual_interest, debt.minimum_payment))                # Calculate credit utilization         ms['total_credit_utilization'] = ms['total_debt']/ms['total_revolving_limit']                # STEP 1. IDENTIFY HOW MUCH CASH IS REQUIRED TO MEET MIN PAYMENTS, AND BORROW MORE IF REQUIRED         logger.debug('\n\nCheck for sufficient cash to make minimum payments\n-------------------------------------------------')        logger.debug('Total cash available: $%6.2f' % (total_cash_available))        logger.debug('Total cash required:  $%6.2f' % (ms['total_min_payments']))        monthly_cash_shortfall = round(ms['total_min_payments'] - total_cash_available, 2)                if monthly_cash_shortfall > 0:                         logger.warning('WARNING! Need $%0.2f more to make minimum payments.' % (monthly_cash_shortfall))                        if monthly_cash_shortfall < ms['total_available_credit']:                                logger.debug('Attempting to withdraw $%0.2f from revolving credit to meet min payments' % (monthly_cash_shortfall))                amount_withdrawn = borrow_from_lowest_interest_product(monthly_cash_shortfall, debts)                total_cash_available += amount_withdrawn                ms['total_shortfall'] += amount_withdrawn                 logger.debug ('Successfully withdrew $%0.2f to cover monthly shortfall\n' % (amount_withdrawn))            else:                 raise Exception('NOT ENOUGH CREDIT AVAILABLE FOR MINIMUM PAYMENT - GAME OVER')              else:            logger.debug('Sufficient cash available!')                                # STEP 2. MAKE THE MINIMUM PAYMENTS         logger.debug('\n\nMake Minimum Payments\n---------------------')        logger.debug('Total min payments required: $%0.2f' % ms['total_min_payments'])                for debt_name, debt in debts.items():             if debt.balance > 0:                 debt_min_payment = debt.minimum_payment                 debt.payment(debt.minimum_payment)                total_cash_available -= debt_min_payment                logger.debug('\tMade min payment of $%8.2f to %s' % (debt_min_payment, debt_name))        logger.debug('\nCash remaining after all minimum payments: $%0.2f' % (total_cash_available))                # STEP 3. APPLY ANY EXCESS CASH TOWARDS HIGHEST INTERST DEBT               if ms['total_shortfall'] == 0 and total_cash_available > 0:            logger.debug('\n\nMake Extra Payments\n---------------------')            logger.debug('Cash available for extra payments $%0.2f' % (total_cash_available))            total_cash_available = apply_remaining_cash_highest_interest_debts(total_cash_available, debts)        # STEP 4. SAVE ANY MONEY LEFT OVER, FOR THE START OF NEXT MONTH         total_savings += total_cash_available                 # STEP 4. Summarize current status of debts after payments and withdrawals         cs = get_current_state(debts)        logger.debug('\n\nEND OF MONTH %d REPORT\n--------------------' % (m))        logger.debug('\t%-30s \t %11.2f' % ('Total savings', total_savings))        logger.debug('\t%-30s \t %11.2f' % ('Total credit utilization', cs['total_credit_utilization']))        logger.debug('\t%-30s \t $%10.2f' % ('Total available credit', cs['total_available_credit']))        # logger.debug('\t%-30s \t $%10.2f' % ('Total revolving limit', cs['total_revolving_limit']))        logger.debug('\t%-30s \t $%10.2f' % ('Total annual interest', cs['total_annual_interest_due']))        logger.debug('\t%-30s \t $%10.2f' % ('Total debt remaining', cs['total_debt']))        describe_debts(debts) # Summarizes current active debts             results.append(ms)                if cs['total_debt'] == 0:             logger.debug('\n\nCONGRATULATIONS - YOU WILL BE DEBT FREE IN %d MONTH(S)!' % (m))            break         df_results = pd.DataFrame.from_records(results)    # plot_results(df_results)    