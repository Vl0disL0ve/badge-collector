import requests
from ..config import API_BASE_URL

def get_headers(telegram_id=None, token=None):
    """Возвращает заголовки для запросов к API"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def get_user_by_telegram_id(telegram_id):
    """Получить пользователя по telegram_id (через API)"""
    try:
        # Нужен эндпоинт для получения пользователя по telegram_id
        # Пока заглушка
        response = requests.get(
            f"{API_BASE_URL}/telegram/user",
            params={"telegram_id": telegram_id}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_user_token(telegram_id):
    """Получить JWT токен пользователя по telegram_id"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/telegram/auth",
            json={"telegram_id": telegram_id}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except:
        return None

def api_request(endpoint, method="GET", token=None, data=None, files=None):
    """Универсальный запрос к API"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = get_headers(token=token)
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        if files:
            headers.pop("Content-Type", None)
            response = requests.post(url, headers=headers, data=data, files=files)
        else:
            response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        if files:
            headers.pop("Content-Type", None)
            response = requests.put(url, headers=headers, data=data, files=files)
        else:
            response = requests.put(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    if response.status_code >= 400:
        error = response.json() if response.content else {"detail": "Unknown error"}
        raise Exception(error.get("detail", "API error"))
    
    if response.status_code == 204:
        return None
    
    return response.json()

# ========== AUTH ==========

def generate_link_code(token):
    """Сгенерировать код для привязки Telegram"""
    return api_request("/telegram/generate-code", method="POST", token=token)

# ========== CATEGORIES ==========

def get_categories(token):
    return api_request("/categories", token=token)

def create_category(token, name, description=None):
    return api_request("/categories", method="POST", token=token, 
                       data={"name": name, "description": description})

def delete_category(token, category_id):
    return api_request(f"/categories/{category_id}", method="DELETE", token=token)

# ========== SETS ==========

def get_sets(token, category_id=None):
    url = "/sets"
    if category_id:
        url += f"?category_id={category_id}"
    return api_request(url, token=token)

def create_set(token, form_data, files):
    return api_request("/sets", method="POST", token=token, data=form_data, files=files)

def update_set(token, set_id, form_data, files=None):
    return api_request(f"/sets/{set_id}", method="PUT", token=token, data=form_data, files=files)

def delete_set(token, set_id):
    return api_request(f"/sets/{set_id}", method="DELETE", token=token)

# ========== BADGES ==========

def get_badges(token, set_id=None, search=None, condition=None, limit=50, offset=0):
    params = []
    if set_id:
        params.append(f"set_id={set_id}")
    if search:
        params.append(f"search={search}")
    if condition:
        params.append(f"condition={condition}")
    params.append(f"limit={limit}")
    params.append(f"offset={offset}")
    url = f"/badges?{'&'.join(params)}"
    return api_request(url, token=token)

def get_badge(token, badge_id):
    return api_request(f"/badges/{badge_id}", token=token)

def create_badge(token, form_data, files):
    return api_request("/badges", method="POST", token=token, data=form_data, files=files)

def update_badge(token, badge_id, form_data):
    return api_request(f"/badges/{badge_id}", method="PUT", token=token, data=form_data)

def delete_badge(token, badge_id):
    return api_request(f"/badges/{badge_id}", method="DELETE", token=token)

# ========== PHOTOS ==========

def add_photo(token, badge_id, photo_file):
    files = {"photo": photo_file}
    return api_request(f"/badges/{badge_id}/photos", method="POST", token=token, files=files)

def delete_photo(token, badge_id, photo_id):
    return api_request(f"/badges/{badge_id}/photos/{photo_id}", method="DELETE", token=token)

def make_main_photo(token, badge_id, photo_id):
    return api_request(f"/badges/{badge_id}/photos/{photo_id}/make-main", method="PUT", token=token)

# ========== TAGS ==========

def get_tags(token):
    return api_request("/tags", token=token)

# ========== EXPORT ==========

def export_collection(token, set_id=None):
    url = "/export"
    if set_id:
        url += f"?set_id={set_id}"
    return api_request(url, token=token)

# ========== PROFILE ==========

def get_profile(token):
    return api_request("/me", token=token)

# ========== ADMIN ==========

def get_admin_stats(token):
    return api_request("/admin/stats", token=token)

def get_admin_users(token, search=None):
    url = "/admin/users"
    if search:
        url += f"?search={search}"
    return api_request(url, token=token)

def create_admin_user(token, email, password):
    return api_request("/admin/users", method="POST", token=token,
                       data={"email": email, "password": password})

def delete_admin_user(token, user_id):
    return api_request(f"/admin/users/{user_id}", method="DELETE", token=token)