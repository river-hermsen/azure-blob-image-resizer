class Image:
    def __init__(self, id, url, metadata):
        self.id = id
        self.url = url
        self.metadata = metadata

    def __repr__(self):
        return f"Image(id={self.id}, url={self.url}, metadata={self.metadata})"