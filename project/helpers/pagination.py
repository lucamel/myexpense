from math import ceil

class Pagination():
    page = None
    per_page = None
    label = None
    data = None
    total = None

    __request = None

    def __init__(self, query, request, label = "data"):
        if(request.args.get('page')):
            try:
                page = int(request.args.get('page'))
            except (TypeError, ValueError):
                page = 1
        else:
            page = 1
        if(request.args.get('per_page')):
            try:
                per_page = int(request.args.get('per_page'))
            except (TypeError, ValueError):
                per_page = 20
        else:
            per_page = 20
        self.page = page
        self.per_page = per_page
        self.label = label
        self.total = query.count()
        self.data = query.limit(per_page).offset((page - 1) * per_page).all()
        self.__request = request

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages
    
    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    @property
    def prev_num(self):
        """Number of the previuos page"""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_next(self):
        """True if a next page exists"""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1

    def paginated_json(self, data):
        json_response = {}
        json_response = {
            self.label: data,
            "pagination_metadata": {
                "_links" : {
                    "next" : self.next_url,
                    "prevoius" : self.previous_url,
                },
                "page" : self.page,
                "per_page": self.per_page,
                "pages": self.pages,
                "total": self.total
            }
        }
        return json_response

    def get_next_url(self):
        args = self.__request.args.copy()
        if not self.has_next:
            return None
        return self.__request.path + '?' + ''.join(['&%s=%s' % (key, value) for (key, value) in args.items() if key != "page" and key != "per_page"]) + '&page=' + str(self.next_num) + '&per_page=' + str(self.per_page)

    def get_previous_url(self):
        args = self.__request.args.copy()
        if not self.has_prev:
            return None
        return self.__request.path + '?' + ''.join(['&%s=%s' % (key, value) for (key, value) in args.items() if key != "page" and key != "per_page"]) + '&page=' + str(self.prev_num) + '&per_page=' + str(self.per_page)

        
    next_url = property(get_next_url)
    previous_url = property(get_previous_url)