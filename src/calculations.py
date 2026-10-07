def calculate_total_debt(long_term_debt, current_debt, commercial_paper):
    amounts = (long_term_debt, current_debt, commercial_paper)

    if any(amount is None for amount in amounts):
        return None

    return sum(amounts)


def calculate_net_debt(total_debt, cash):
    if total_debt is None or cash is None:
        return None

    return total_debt - cash


def calculate_ratio(numerator, denominator):
    if numerator is None or denominator is None:
        return None

    if denominator <= 0:
        return None

    return numerator / denominator