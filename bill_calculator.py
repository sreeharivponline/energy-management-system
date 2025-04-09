# bill_calculator.py
def calculate_kseb_bill(units, billing_cycle=1, phase='single'):
    """
    Calculate KSEB electricity bill based on units consumed, billing cycle, and phase.
    :param units: Total units consumed in the billing period
    :param billing_cycle: 1 for monthly, 2 for bi-monthly
    :param phase: 'single' for single-phase, 'three' for three-phase
    :return: Dictionary with bill breakdown
    """
    # Adjust units for billing cycle (get average monthly consumption)
    monthly_units = units / billing_cycle if billing_cycle > 0 else units

    # Telescopic tariff slabs (up to 250 units)
    telescopic_slabs = [
        (50, 3.25),  # 0-50 units: ₹3.25/unit
        (100, 4.05),  # 51-100 units: ₹4.05/unit
        (150, 5.10),  # 101-150 units: ₹5.10/unit
        (200, 6.95),  # 151-200 units: ₹6.95/unit
        (250, 8.20),  # 201-250 units: ₹8.20/unit
    ]

    # Non-telescopic tariff slabs (above 250 units)
    non_telescopic_slabs = [
        (300, 6.40),  # 0-300 units: ₹6.40/unit
        (350, 7.25),  # 0-350 units: ₹7.25/unit
        (400, 7.60),  # 0-400 units: ₹7.60/unit
        (500, 7.90),  # 0-500 units: ₹7.90/unit
        (float('inf'), 8.80),  # Above 500 units: ₹8.80/unit
    ]

    # Fixed charges (single-phase)
    fixed_charges_single = [
        (100, 65),  # 0-100 units: ₹65/month
        (150, 75),  # 101-150 units: ₹75/month
        (200, 85),  # 151-200 units: ₹85/month
        (250, 95),  # 201-250 units: ₹95/month
        (300, 135),  # 251-300 units: ₹135/month
        (500, 145),  # 301-500 units: ₹145/month
        (float('inf'), 155),  # Above 500 units: ₹155/month
    ]

    # Fixed charges (three-phase)
    fixed_charges_three = [
        (100, 140),  # 0-100 units: ₹140/month
        (150, 150),  # 101-150 units: ₹150/month
        (200, 160),  # 151-200 units: ₹160/month
        (250, 170),  # 201-250 units: ₹170/month
        (300, 210),  # 251-300 units: ₹210/month
        (500, 220),  # 301-500 units: ₹220/month
        (float('inf'), 230),  # Above 500 units: ₹230/month
    ]

    # Calculate energy charge
    energy_charge = 0
    remaining_units = monthly_units

    if monthly_units <= 250:
        # Telescopic billing
        for slab_limit, rate in telescopic_slabs:
            if remaining_units <= 0:
                break
            # Calculate units in this slab
            units_in_slab = min(remaining_units, slab_limit - (slab_limit - 50 if slab_limit > 50 else 0))
            if remaining_units > (slab_limit - 50 if slab_limit > 50 else remaining_units):
                energy_charge += units_in_slab * rate
                remaining_units -= units_in_slab
            else:
                energy_charge += remaining_units * rate
                remaining_units = 0
    else:
        # Non-telescopic billing
        for slab_limit, rate in non_telescopic_slabs:
            if monthly_units <= slab_limit:
                energy_charge = monthly_units * rate
                break

    # Scale energy charge for the billing cycle
    energy_charge *= billing_cycle

    # Calculate fixed charge
    fixed_charge = 0
    fixed_charge_table = fixed_charges_single if phase == 'single' else fixed_charges_three
    for slab_limit, charge in fixed_charge_table:
        if monthly_units <= slab_limit:
            fixed_charge = charge * billing_cycle
            break

    # Additional charges
    surcharge = units * 0.001  # 0.1 paise per unit = ₹0.001/unit
    meter_rent = 10 * billing_cycle  # ₹10/month
    subtotal = energy_charge + fixed_charge + surcharge + meter_rent
    gst = subtotal * 0.05  # 5% GST
    total = subtotal + gst

    return {
        'energy_charge': round(energy_charge, 2),
        'fixed_charge': round(fixed_charge, 2),
        'surcharge': round(surcharge, 2),
        'meter_rent': round(meter_rent, 2),
        'subtotal': round(subtotal, 2),
        'gst': round(gst, 2),
        'total': round(total, 2)
    }