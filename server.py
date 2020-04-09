from aiohttp import web

import logging
import traceback

import resolver

# used to store cached dns responses
cache = {}

logging.basicConfig(format="%(asctime)-15s >>> %(message)s",
                    level=logging.ERROR)
logger = logging.getLogger("dns_server")
logger.setLevel(level=logging.DEBUG)


def process_trace(trace):
    processed_trace = []
    for trace_record in trace:
        trace_record_dict = trace_record._asdict()
        trace_record_dict["request_addr"] = trace_record_dict["request_addr"]._asdict()
        trace_record_dict["response"] = trace_record_dict["response"]._asdict()
        processed_trace.append(trace_record_dict)
    return processed_trace


# noinspection PyBroadException
async def resolve(request: web.Request):
    try:
        target_host = request.rel_url.query['domain']
        need_trace = True if request.rel_url.query['trace'] == "true" else False
        trace = resolver.resolve(target_host, need_trace)
        return web.json_response({
            "status": "success",
            "response": process_trace(trace)
        })
    except Exception:
        return web.json_response({
            "status": "fail",
            "error": str(traceback.format_exc())
        })


if __name__ == "__main__":
    app = web.Application()
    app.add_routes([
        web.get("/get-a-records", resolve)
    ])
    web.run_app(app, host="::", port=8080)
