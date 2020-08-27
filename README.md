# URL-fuse powered by open-resty
a configurable URL curcuit breaker for nginx/openresty 
这是一个可配置的 URL断路器(熔断器), 基于 nginx openresty.

# Why
我们不希望整体服务被个别接口的慢请求拖死. 因为慢请求会不断堆积, 使服务出现超时499或502, 最后504.


# How
慢请求雪崩一般是网络IO问题, 也可能是 计算缓慢(Load 高或计算复杂)等原因,而这些服务一般通过 fastcgi/uwsgi/proxy/..返回内容, 所以内容生成(content_by_lua)前后时间差就是真实的执行时间,  它是从接受请求第一个字节到返回响应最后一个字符的时间段(ngx.now()-ngx.req.start_time). 

当有连续多个请求时, 请求数量大于一个阀值则可以认为此 domain+path 的接口服务高风险 或失败请求.这里需要做熔断来降级此接口,防止雪崩扩大.

# Design
![design](./design.png '设计')

# Notice
 - 为了能正常计算 程序的执行时间, REQUEST_TIMEOUT 要小于cgi/fastcgi/uwsgi/proxy_pass 的最大超时也小于 nginx 对应的超时时间. 否则执行时间计算不准确.
 - 如果在熔断之前瞬间有大量请求打入 nginx, 则服务依然可能会雪崩.
 - 具体配置请参考 nginx.conf.
 


# Test
```
#macbook pro 上
ab -k -c 300 -n5000 127.0.0.1/ | grep 'Requests per second:'

#nginx.conf 
bash-3.2$ ab -k -c 300 -n5000 127.0.0.1/ | grep 'Requests per second:'
Completed 500 requests
Completed 1000 requests
Completed 1500 requests
Completed 2000 requests
Completed 2500 requests
Completed 3000 requests
Completed 3500 requests
Completed 4000 requests
Completed 4500 requests
Completed 5000 requests
Finished 5000 requests
Requests per second:    2754.05 [#/sec] (mean)


#benchmark.nginx.conf:  openresty with URL-fuse 
bash-3.2$ ab -k -c 300 -n5000 127.0.0.1/ | grep 'Requests per second:'
Completed 500 requests
Completed 1000 requests
Completed 1500 requests
Completed 2000 requests
Completed 2500 requests
Completed 3000 requests
Completed 3500 requests
Completed 4000 requests
Completed 4500 requests
Completed 5000 requests
Finished 5000 requests
Requests per second:    2493.06 [#/sec] (mean)
```


