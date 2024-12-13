import math

from django import template

register = template.Library()


@register.filter
def round_uncertainty(uncertainty):
    if uncertainty == 0:
        return "0"

    # order of magnitude of the uncertainty
    magnitude = math.floor(math.log10(uncertainty))
    first_digit = uncertainty / (10**magnitude)

    # Use 2 significant figures for values starting with 1 or 2, otherwise use 1
    sig_figs = 2 if first_digit < 3 else 1

    uncertainty_str = str(uncertainty)
    if len(uncertainty_str.replace("0.", "")) <= sig_figs:
        return uncertainty_str

    # scale for rounding to desired significant figures
    scale = 10 ** (sig_figs - magnitude - 1)

    # round and convert back to string to remove unneeded zeros
    return str(round(uncertainty * scale) / scale)


@register.filter
def format_magnitude(value, uncertainty):
    """
    Combines roundUncertainty and roundMagnitude operations into a single filter
    """
    # Handle None cases
    if uncertainty is None or value is None:
        return "N/A"

    if uncertainty == 0:
        return str(value)

    # First round the uncertainty (copied from round_uncertainty)
    magnitude = math.floor(math.log10(uncertainty))
    first_digit = uncertainty / (10**magnitude)
    sig_figs = 2 if first_digit < 3 else 1

    uncertainty_str = str(uncertainty)
    if len(uncertainty_str.replace("0.", "")) <= sig_figs:
        rounded_uncertainty = uncertainty_str
    else:
        scale = 10 ** (sig_figs - magnitude - 1)
        rounded_uncertainty = str(round(uncertainty * scale) / scale)

    # Now handle the magnitude value using the rounded uncertainty
    uncertainty = float(rounded_uncertainty)
    uncertainty_decimal_places = (
        len(rounded_uncertainty.split(".")[-1]) if "." in rounded_uncertainty else 0
    )

    # get the decimal places in the original value
    value_str = str(value)
    value_decimal_places = len(value_str.split(".")[-1]) if "." in value_str else 0

    # use at least one decimal place for uncertainties between 0.1 and 1
    min_decimal_places = 1 if (uncertainty >= 0.1 and uncertainty < 1) else 0

    # Get final number of decimal places
    final_decimal_places = max(
        min_decimal_places, min(uncertainty_decimal_places, value_decimal_places)
    )

    return f"{value:.{final_decimal_places}f}"
