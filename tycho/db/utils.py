class async_generator:
    '''
        We dont want application layer to directly interact
        with Mongo's cursor. This class acts as middle man
        between Mongo and app codeby encapsulating Mongo's
        cursor and providing iterator to client code.
        Use 'async for' to iterate on the returned object.
    '''

    def __init__(self, cursor, map):
        self.cursor = cursor
        self.map = map

    async def __aiter__(self):
        return self

    async def __anext__(self):
        async for doc in self.cursor:
            return self.map(doc)
        else:
            raise StopAsyncIteration
