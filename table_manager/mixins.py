import base64


class StackMixin:
    def clear_stack(self, request):
        request.session["call_stack"] = []

    def get(self, request, *args, **kwargs):
        """ get pushes any return path on to the stack """
        return_path = request.GET.get("return", None)
        if return_path:
            stack = request.session.get("call_stack", [])
            stack.append([request.path, return_path])
            request.session["call_stack"] = stack
            print("GET", stack)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Add the current path, minus any return information, to the context """
        context = super().get_context_data(**kwargs)
        url = self.request.path  # .urlencode()
        query = self.request.GET.urlencode()
        query = query[: query.find("return=")]
        if query:
            url += f"?{query}"
        return context

    def get_success_url(self):
        """ pop the stack and return to that view """
        stack = self.request.session.get("call_stack", None)
        entry = None
        while stack:
            entry = stack.pop()
            if entry[0] == self.request.path:
                url = entry[1]
                print("popped", url, stack)
                return url
        self.request.session["call_stack"] = []
        return entry[1] if entry else "/"
