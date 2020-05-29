import collections
import logging
import socket
import time
import typing

import dns.message
import dns.query
import dns.rdataclass
import dns.rdatatype
import dns.resolver

logging.basicConfig(format="%(message)s", level=logging.ERROR)
logger = logging.getLogger("resolver")
logger.setLevel(level=logging.INFO)

DNSRecord = collections.namedtuple("DNSRecord", ["name", "address", "ttl", "ts"])
TraceRecord = collections.namedtuple("TraceRecord", ["request_addr", "request_type", "response"])

cache_authority = dict()
cache_address = dict()


def resolve(target_host, need_trace=False):
    target_host = target_host.lower()
    if not target_host.endswith("."):
        target_host += "."
    logger.info(f"resolve: {target_host}, need_trace: {need_trace}")

    prev_server: typing.Optional[DNSRecord] = None
    curr_server: DNSRecord = DNSRecord(name="a.root-servers.net.",
                                       address=socket.gethostbyname("a.root-servers.net."),
                                       ttl=None, ts=None)

    trace = []

    # try using cache
    if not need_trace:
        # check address cache
        if target_host in cache_address:
            if cache_address[target_host].ts + cache_address[target_host].ttl > time.time():
                trace = [TraceRecord(request_addr=DNSRecord(name="cache", address=None, ttl=None, ts=None),
                                     request_type="A", response=cache_address[target_host])]
                return trace
            else:
                cache_address.pop(target_host)

        # check authority cache
        subs = []
        if not target_host.endswith("."):
            target_host += "."
        index = target_host.rfind(".", 0, len(target_host) - 1)
        while index != -1:
            subs.append(target_host[index:].lstrip("."))
            index = target_host.rfind(".", 0, index)
        subs.append(target_host)
        subs = list(reversed(subs))
        for s in subs:
            if s in cache_authority:
                if cache_authority[s].ts + cache_authority[s].ttl > time.time():
                    # update curr_server for faster resolve path
                    curr_server = cache_authority[s]
                    trace.append(TraceRecord(request_addr=DNSRecord(name="cache", address=None, ttl=None, ts=None),
                                             request_type="NS", response=curr_server))
                    break
                else:
                    cache_authority.pop(s)

    # find NS
    while not prev_server or prev_server.name != curr_server.name:
        curr_ts = int(time.time())
        query_host = dns.name.from_text(target_host)
        query = dns.message.make_query(query_host, dns.rdatatype.NS)
        response = dns.query.tcp(query, curr_server.address)

        # if response has answer - found final NS
        if len(response.answer) > 0 and len(response.authority) == 0:
            break

        # if response has SOA in authority - found final NS
        if len(response.authority) == 1 and response.authority[0].rdtype == dns.rdatatype.SOA:
            break

        # find best authority:
        best_authority = None
        for authority in response.authority:
            if not target_host.endswith(str(authority.name).lower()):
                continue
            if not best_authority or len(str(authority.name)) > len(str(authority.name)):
                best_authority = authority
        best_authority_ttl = int(best_authority.ttl)

        # find authority server address:
        authority_server_name, authority_server_addr, authority_server_ttl = None, None, None
        for authority_server in best_authority:
            authority_server_name = str(authority_server)
            for additional_record in response.additional:
                if str(additional_record.name).lower() == str(authority_server).lower() and \
                        additional_record.rdtype == dns.rdatatype.A:
                    authority_server_addr = str(additional_record[0])
                    authority_server_ttl = int(additional_record.ttl)
                    break
            if authority_server_addr:
                break

        # failed to find authority_server_addr in response.additional - full resolve
        if not authority_server_addr:
            resolved_authority = resolve(authority_server_name, False)[-1]
            # need to update curr_ts, because "resolve" can use cached record for authority_server_name
            authority_server_addr, authority_server_ttl, curr_ts = \
                resolved_authority.response.address, resolved_authority.response.ttl, resolved_authority.response.ts

        authority_ttl = min(best_authority_ttl, authority_server_ttl)

        # save resolved authority - can use it in next requests:
        cache_authority[str(best_authority.name)] = DNSRecord(
            name=authority_server_name,
            address=authority_server_addr,
            ttl=authority_ttl,
            ts=curr_ts
        )

        prev_server = curr_server
        curr_server = DNSRecord(name=authority_server_name, address=authority_server_addr,
                                ttl=authority_ttl, ts=curr_ts)
        logger.info(f"request {dns.rdatatype.to_text(dns.rdatatype.NS)} for {query_host} to {prev_server} "
                    f"=> response: {curr_server}")
        trace.append(TraceRecord(request_type="NS", request_addr=prev_server, response=curr_server))

    # find A
    curr_ts = int(time.time())
    query_host = dns.name.from_text(target_host)
    query = dns.message.make_query(query_host, dns.rdatatype.A)
    response = dns.query.tcp(query, curr_server[1])

    if response.answer:
        # answer can contain aliases
        target_host_record, aliases = None, dict()
        for answer in response.answer:
            if answer.rdtype in [dns.rdatatype.CNAME, dns.rdatatype.A]:
                answer_record = DNSRecord(name=str(answer.name), address=str(answer[0]),
                                          ts=curr_ts, ttl=int(answer.ttl))
                if str(answer.name) == target_host:
                    target_host_record = answer_record
                aliases[str(answer.name)] = answer_record
        # target_host_record is required
        assert target_host_record

        result = target_host_record
        ttl = target_host_record.ttl  # find minimal ttl
        while result.address in aliases:
            result = aliases[result.address]
            if result.ttl < ttl:
                ttl = result.ttl

        # store every alias in cache:
        for alias in aliases.values():
            cache_address[alias.name] = DNSRecord(name=alias.name, address=result.address, ttl=ttl, ts=curr_ts)
        response = DNSRecord(name=target_host, address=result.address, ttl=ttl, ts=result.ts)
        cache_address[target_host] = response
    else:
        # no such address
        response = DNSRecord(name=target_host, address=None, ts=curr_ts, ttl=None)
    logger.info(f"request {dns.rdatatype.to_text(dns.rdatatype.A)} "
                f"for {query_host} to {curr_server} => response: {response}")
    trace.append(TraceRecord(
        request_type="A",
        request_addr=curr_server,
        response=response
    ))

    return trace
