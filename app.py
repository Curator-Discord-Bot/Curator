from .bot import run_bot

bot = None


def application(env, start_response):
    global bot
    start_response('200 OK', [('Content-Type', 'text/html')])
    bot = bot or run_bot()
    return [b"Hello World"]
