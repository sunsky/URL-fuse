# URL-fuse powered by open-resty
configurable URL curcuit breaker for nginx/openresty 

# Why
我们不希望整体服务被个别接口的慢请求拖死. 因为慢请求会不断堆积, 使服务出现超时499或502, 最后504.


# How
慢请求雪崩一般是网络IO问题, 也可能是 计算缓慢(Load 高或计算复杂)等原因,而这些服务一般通过 fastcgi/uwsgi/proxy/..返回内容, 所以内容生成(content_by_lua)前后时间差就是真实的执行时间,  它是从接受请求第一个字节到返回响应最后一个字符的时间段(ngx.now()-ngx.req.start_time). 

当有连续多个请求时, 请求数量大于一个阀值则可以认为此 domain+path 的接口服务高风险 或失败请求.这里需要做熔断来降级此接口,防止雪崩扩大.

# Design


# Notice
 为了能正常计算 程序的执行时间, REQUEST_TIMEOUT 要小于cgi/fastcgi/uwsgi/proxy_pass 的最大超时也小于 nginx 对应的超时时间. 否则执行时间计算不准确.


# Test



