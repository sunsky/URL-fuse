# URL-fuse powered by openresty
a configurable URL curcuit breaker for nginx/openresty 

这是一个可灵活配置的URL断路器(熔断器), 基于 nginx openresty.

# Why
我们不希望整体服务被个别接口的慢请求拖死. 因为慢请求会不断堆积, 使服务出现超时499或502, 最后504. 

同时你也可以将糟糕的慢请求(比如15秒内连续10次5秒超时)做成服务健康报警, 这样能提前减少流量增加时的雪崩概率.


# How
慢请求雪崩一般是网络IO问题, 也可能是 计算缓慢(Load 高或计算复杂)等原因,而这些服务一般通过 fastcgi/uwsgi/proxy/..返回内容, 所以内容生成(content_by_lua)前后时间差就是真实的执行时间,  它是从接受请求第一个字节到返回响应最后一个字符的时间段(ngx.now()-ngx.req.start_time). 

当有连续多个请求时, 请求数量大于一个阀值则可以认为此 domain+path 的接口服务高风险 或失败请求.这里需要做熔断来降级此接口,防止雪崩扩大.

# Design
![design](./design.png '设计')

# Notice
 - 为了能正常计算 程序的执行时间, REQUEST_TIMEOUT 要小于cgi/fastcgi/uwsgi/proxy_pass 的最大超时也小于 nginx 对应的超时时间. 否则执行时间计算不准确.
 - 如果在熔断之前瞬间有大量请求打入 nginx, 则服务依然可能会雪崩.
 - 具体配置请参考 nginx.conf.
 
# Configure
```nginx
http{
    #... somethings 
    
    # url-fuse start
	lua_package_path '/data1/ms/front/docker/config/openresty/?.lua;;'; --your directory of lua files
	lua_shared_dict fuse_shard_dict 10m; --change for your case
	init_worker_by_lua_block {
			local fuse = require "url_fuse"
			fuse:setup(function(this)  
				this.LIFETIME = 10
				this.FAILS_LIMIT = 10
				this.REQUEST_TIMEOUT =5
				this.FUSED_DURATION = 5
			end)
	}
	server {
		listen  80;
		root    /data1/ms/front/;

		location ~ ^/.*(\.js|\.css|\.png|\.gif|\.jpg|favicon\.ico)$ {
			log_not_found off;
			access_log    off;
		}
		location / {
			access_by_lua_block {
				local fuse = require "url_fuse"
				fuse:run_access()
			}

			log_by_lua_block {
				local fuse = require "url_fuse"
				fuse:run_log()
			}
			return 200 'hello';
		}
	}
    #url-fuse end
}

```
# support params 
```lua
local config  = {
    dict = ngx.shared.fuse_shard_dict,
    -- config start
    REQUEST_TIMEOUT = 1, --in seconds
    FUSED_DURATION = 10, --in seconds
    FAILS_LIMIT = 10, --number of consecutive failures
    LIFETIME = 15, -- expired counters will be discarded, in seconds
    DEBUG = false,
    GEN_BUCKET_ID = function(self)
        return table.concat({ ngx.var.host, ngx.var.uri })
    end,
    ON_DEGRADED_CALLBACK = function(self)
        ngx.status = 403
        return ngx.exit(403)
    end,
    BEFORE_HALF_OPEN_CALLBACK = function(self)
    end,
    AFTER_HALF_OPEN_CALLBACK = function(self)
    end,
    VALIDATE_REQUEST = function(self)
        --true is success
        local elapsed = ngx.now() - ngx.req.start_time()
        return elapsed < self.REQUEST_TIMEOUT
    end,
}
```
usage:
```lua
local fuse = require "url_fuse"
fuse:setup(function(this)  --set your params
    this.LIFETIME = 10
    --bla bla ...
end)
```

# Test
```shell script
ab -X 127.0.0.1:80  -c 1000 -n 10000 -k  'http://test.cn/a/'
```

```shell script
# use nginx.conf 
Server Software:        openresty
Server Hostname:        test.cn
Server Port:            80

Document Path:          /a/
Document Length:        5 bytes

Concurrency Level:      1000
Time taken for tests:   0.250 seconds
Complete requests:      10000
Failed requests:        0
Write errors:           0
Keep-Alive requests:    10000
Total transferred:      1490000 bytes
HTML transferred:       50000 bytes
Requests per second:    40022.09 [#/sec] (mean)
Time per request:       24.986 [ms] (mean)
Time per request:       0.025 [ms] (mean, across all concurrent requests)
Transfer rate:          5823.53 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    4  13.1      0      64
Processing:     3   17   3.1     17      65
Waiting:        1   17   3.1     17      35
Total:          3   21  14.6     17      88



# use benchmark.nginx.conf, ( openresty with URL-fuse ) 
Server Software:        openresty
Server Hostname:        test.cn
Server Port:            80

Document Path:          /a/
Document Length:        5 bytes

Concurrency Level:      1000
Time taken for tests:   0.252 seconds
Complete requests:      10000
Failed requests:        0
Write errors:           0
Keep-Alive requests:    10000
Total transferred:      1490000 bytes
HTML transferred:       50000 bytes
Requests per second:    39737.26 [#/sec] (mean)
Time per request:       25.165 [ms] (mean)
Time per request:       0.025 [ms] (mean, across all concurrent requests)
Transfer rate:          5782.08 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    4  12.9      0      62
Processing:     3   17   3.0     18      63
Waiting:        1   17   3.0     18      36
Total:          3   22  14.5     18      87

```
openresty version:
```shell script
bash-4.3# nginx -V
nginx version: openresty/1.17.8.2
built by gcc 5.3.0 (Alpine 5.3.0) 
built with OpenSSL 1.0.2n  7 Dec 2017
TLS SNI support enabled
configure arguments: --prefix=/usr/local/sinawap/nginx/nginx --with-cc-opt=-O2 --add-module=../ngx_devel_kit-0.3.1 --add-module=../echo-nginx-module-0.62 --add-module=../xss-nginx-module-0.06 --add-module=../ngx_coolkit-0.2 --add-module=../set-misc-nginx-module-0.32 --add-module=../form-input-nginx-module-0.12 --add-module=../encrypted-session-nginx-module-0.08 --add-module=../srcache-nginx-module-0.32 --add-module=../ngx_lua-0.10.17 --add-module=../ngx_lua_upstream-0.07 --add-module=../headers-more-nginx-module-0.33 --add-module=../array-var-nginx-module-0.05 --add-module=../rds-json-nginx-module-0.15 --add-module=../ngx_stream_lua-0.0.8 --with-ld-opt=-Wl,-rpath,/usr/local/sinawap/nginx/luajit/lib --with-threads --with-file-aio --with-http_realip_module --with-http_gzip_static_module --with-pcre-jit --with-ipv6 --with-http_stub_status_module --with-stream --with-stream_ssl_module --with-stream_ssl_preread_module --with-http_ssl_module
```

取多次均值: nginx : 40022 vs url-fuse: 39737, 性能损耗可忽略


