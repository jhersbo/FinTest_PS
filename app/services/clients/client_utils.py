import asyncio

def ratelimit(rl_limit:float=0.1):
    """
    Decorator which awaits calling this method by a given number of seconds.
    Decorated functions must be defined as async and calling functions must be awaited
    """
    def d(fn):
        async def w(*args: any, **kwargs: any):
            await asyncio.sleep(rl_limit)
            return await fn(*args, **kwargs)
        return w
    return d