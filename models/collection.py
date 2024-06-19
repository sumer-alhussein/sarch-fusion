class Category:
    def __init__(self, name, id=None, description=None, subcategories=None):
        self.id = id
        self.name = name
        self.description = description
        self.subcategories = subcategories or []

    def add_subcatogries(self, name, id):
        self.subcategories.append(
            {'id': id, 'name': name})
