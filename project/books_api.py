import requests


class gbooks():
    googleapikey = "AIzaSyDnfRwjhrvfq3n-Rb85k1tBcqxcgeDchSg"

    def search(self, value):
        parms = {"q": value, 'key': self.googleapikey}
        response = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=parms)
        rj = response.json()
        items = []
        for i in rj["items"]:
            try:
                items.append(repr(i["volumeInfo"]["description"]))
            except:
                pass
        if bool(items):
            return items[0][1:-1]
        return "Sorry, we have no description of this book..."