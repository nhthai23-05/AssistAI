"""Quy đổi danh mục của từng dataset về 13 danh mục chi của AssistAI (dropdown ở tab "Tóm tắt", B26:B41).

Danh mục AssistAI lấy từ frontend/src/data/expenses.js. Ba danh mục "Nợ", "Đầu tư", "Quà tặng"
không có tương ứng rõ trong Sparkov / Personal Budget; TabFormer chỉ có "Quà tặng" (hoa, quà lưu niệm).
"""

ASSISTAI = ["Ăn uống", "Đi lại", "Nhà", "Cá nhân", "Sức khỏe/y tế", "Vui chơi giải trí", "Nghe gọi",
            "Giáo dục", "Công việc", "Quà tặng", "Đầu tư", "Nợ", "Khác"]

SPARKOV = {
    "grocery_pos": "Ăn uống", "grocery_net": "Ăn uống", "food_dining": "Ăn uống",
    "gas_transport": "Đi lại",
    "home": "Nhà",
    "shopping_pos": "Cá nhân", "shopping_net": "Cá nhân", "personal_care": "Cá nhân",
    "health_fitness": "Sức khỏe/y tế",
    "entertainment": "Vui chơi giải trí", "travel": "Vui chơi giải trí",
    "misc_pos": "Khác", "misc_net": "Khác", "kids_pets": "Khác",
}

PERSONAL_BUDGET = {
    "Coffe": "Ăn uống", "Market": "Ăn uống", "Restuarant": "Ăn uống", "Business lunch": "Ăn uống",
    "Transport": "Đi lại", "Taxi": "Đi lại", "Fuel": "Đi lại", "Rent Car": "Đi lại",
    "Communal": "Nhà",
    "Clothing": "Cá nhân", "Tech": "Cá nhân",
    "Health": "Sức khỏe/y tế", "Sport": "Sức khỏe/y tế",
    "Events": "Vui chơi giải trí", "joy": "Vui chơi giải trí", "Film/enjoyment": "Vui chơi giải trí",
    "Travel": "Vui chơi giải trí", "Motel": "Vui chơi giải trí",
    "Phone": "Nghe gọi",
    "Learning": "Giáo dục",
    "business_expenses": "Công việc",
    "Other": "Khác",
}

# MCC (Merchant Category Code, ISO 18245) → AssistAI. Mã không có trong bảng rơi vào "Khác".
_MCC = {
    "Ăn uống": [5300, 5411, 5422, 5441, 5451, 5462, 5499, 5812, 5813, 5814, 5921],
    "Đi lại": [4111, 4112, 4121, 4131, 4784, 5533, 5541, 5542, 7531, 7538, 7542, 7549],
    "Nhà": [1711, 4900, 5200, 5211, 5251, 5261, 5712, 5719, 5722, 7349],
    "Cá nhân": [5045, 5094, 5310, 5311, 5651, 5655, 5661, 5732, 5733, 5815, 5816, 5932, 5941, 5970, 7210, 7230],
    "Sức khỏe/y tế": [5912, 5977, 8011, 8021, 8041, 8043, 8049, 8062, 8099],
    "Vui chơi giải trí": [4411, 4511, 4722, 7011, 7801, 7802, 7832, 7922, 7995, 7996],
    "Nghe gọi": [4814, 4899],
    "Giáo dục": [5942, 8220, 8299],
    "Công việc": [4214, 7393, 8111, 8931],
    "Quà tặng": [5193, 5947],
}
MCC = {code: cat for cat, codes in _MCC.items() for code in codes}


def mcc_to_assistai(code: int) -> str:
    if code in MCC:
        return MCC[code]
    if 3000 <= code <= 3299 or 3500 <= code <= 3999:  # hãng bay, khách sạn
        return "Vui chơi giải trí"
    if 3300 <= code <= 3499:  # thuê xe
        return "Đi lại"
    return "Khác"  # gồm 4829 chuyển tiền, 6300 bảo hiểm, 9402 bưu điện
