from ..constants import COLLECTIONS
from ..models import Category


def get_user_collections() -> list[Category]:
    categories: list[Category] = []
    for category_data in COLLECTIONS:
        category = Category(
            name=category_data['name'], id=category_data['id'], description=category_data['description'])
        for subcategory_data in category_data['subcategories']:
            category.add_subcatogries(
                name=subcategory_data['name'], id=subcategory_data['id'])
        categories.append(category)
    return categories
