"""
Traducción de características financieras al español mexicano
"""

FEATURE_TRANSLATIONS = {
    # Variables originales en inglés -> Español mexicano
    'out_prncp': 'Saldo Capital Pendiente',
    'out_prncp_inv': 'Saldo Inversionistas Pendiente',
    'last_pymnt_amnt': 'Monto Último Pago',
    'total_rec_prncp': 'Total Capital Recibido',
    'recoveries': 'Cobranza Recuperada',
    'collection_recovery_fee': 'Comisión de Cobranza',
    'total_pymnt': 'Total Pagado',
    'installment': 'Pago Mensual (Mensualidad)',
    'funded_amnt_inv': 'Monto Financiado por Inversionistas',
    'total_pymnt_inv': 'Total Pagado a Inversionistas',
    'total_rec_int': 'Total Intereses Recibidos',
    'hardship_payoff_balance_amount': 'Saldo Liquidación por Dificultad',
    'orig_projected_additional_accrued_interest': 'Interés Devengado Proyectado',
    'int_rate': 'Tasa de Interés Anual',
    'hardship_amount': 'Monto por Dificultad Financiera',
    'total_rec_late_fee': 'Total Recargos por Mora',
    'hardship_last_payment_amount': 'Último Pago por Dificultad',
    'dti': 'Relación Deuda/Ingreso (DTI)',
    'annual_inc': 'Ingreso Anual Bruto',
    'bc_util': 'Utilización de Crédito (Buró)'
}

# Categorías para agrupar características
FEATURE_CATEGORIES = {
    'Deuda y Pagos': [
        'out_prncp', 'out_prncp_inv', 'last_pymnt_amnt',
        'total_rec_prncp', 'total_pymnt', 'installment'
    ],
    'Recuperaciones y Moratorios': [
        'recoveries', 'collection_recovery_fee',
        'total_rec_late_fee'
    ],
    'Inversionistas': [
        'funded_amnt_inv', 'total_pymnt_inv'
    ],
    'Intereses': [
        'total_rec_int', 'int_rate',
        'orig_projected_additional_accrued_interest'
    ],
    'Situaciones de Dificultad': [
        'hardship_payoff_balance_amount', 'hardship_amount',
        'hardship_last_payment_amount'
    ],
    'Perfil del Solicitante': [
        'dti', 'annual_inc', 'bc_util'
    ]
}

# Ayudas contextuales específicas para México
FEATURE_HELP_TEXTS = {
    'out_prncp': 'Cantidad de capital principal que aún debe pagarse (en pesos mexicanos)',
    'dti': 'Porcentaje del ingreso mensual que se destina al pago de deudas. En México, idealmente menor al 40%',
    'int_rate': 'Tasa de interés anual (CAT puede ser diferente). Valores típicos en México: 15%-40% anual',
    'annual_inc': 'Ingreso anual antes de impuestos. Considerar ingresos formales e informales según el perfil',
    'bc_util': 'Porcentaje del límite de crédito utilizado en Buró de Crédito. Recomendado <30%',
    'bc_util': 'Porcentaje de utilización de tus líneas de crédito reportadas en Buró de Crédito',
    'recoveries': 'Montos recuperados por cobranza judicial o extrajudicial',
    'collection_recovery_fee': 'Comisión que cobran las empresas de cobranza en México (típicamente 20-30%)'
}