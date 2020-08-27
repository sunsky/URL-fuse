#!env python3
import requests
import time
import json
import random
MEAN_ERROR=0.5
REQUEST_TIMEOUT = 0.5
LIFETIME = 20
FAILS_LIMIT = 2
FAILS_CODE = 403
FUSED_DURATION = 5

randURLPath=random.randint(0, 999999)
print('randURLPath ', randURLPath)
def get(action,sleep=0,):
    global randURLPath
    url='http://test.cn/unittest/%s?sleep=%s&action=%s#e=f'%(randURLPath, sleep, action)
    rand=random.randint(0,99999)
    print("get url %s&rand=%s now: %s "%(url, rand, time.time()))
    result = requests.get(url,params={'rand':rand},proxies={'http': 'http://127.0.0.1'})
    return result,url

def testLoop(headerKey):
    i=0
    lastCode=None
    start=time.time()
    res=None
    url=None
    while True:
        res,url=mockRequest(i,success=False, action='loop'+str(randURLPath))
        if lastCode and lastCode != res.status_code :
            print('http code changed: %s => %s ,break'%(lastCode, res.status_code))
            break

        lastCode = res.status_code
        ret=assertRequest(url=url,result=res,done=False, code=FAILS_CODE, willEnd=True,header_key=headerKey)
        time.sleep(0.2) #avoid too many
        i+=1
    elapsed = time.time()-start
    if abs(elapsed - FUSED_DURATION)>1 : 
        print("elapsed %d not equal FUSED_DURATION %d " %(int(elapsed), FUSED_DURATION))
        assert False
    return res,url

start = time.time()
fusedEnd=None
def mockRequest(i,success=True, action=''):
    result,url = get(action, 0 if success  else  REQUEST_TIMEOUT)
    return result,url

def assertRequest(result,url=None,code=200, done=True, header_key=None,willEnd=False, willFails=None, ):
    try:
        resObj = json.loads(result.content) 
        if willFails!=None :
            assert resObj['fail_count'] == willFails
        assert result.status_code == code
        if done:
            assert result.content.rfind(b'done') > 0
        else:
            assert result.content.rfind(b'done') == -1

        if header_key:
            assert result.headers.get(header_key) == '1'
    except Exception as e:
        print(result.status_code, url, result.headers,  result.content.decode('utf8'))
        raise e

print('start testing')
print('mock success')
i=0
while i<10:
    i+=1
    res,url=mockRequest(i,success=True, action='ok'+str(randURLPath))
    assertRequest(url=url,result=res,done=True)

print('trigger fused', )
i=0
while i<FAILS_LIMIT: 
    res,url=mockRequest(i,success=False,action='trigger_fused'+str(randURLPath))
    assertRequest(url=url,result=res,done=True)
    i+=1

print('fused, and reject')
res,url=testLoop('x-in-degraded')

print('do half-open')
i=0
ret=assertRequest(url=url,result=res,done=True, header_key='x-before-half-open')

print('after half-open, it will be degraded with x-in-degraded')
res,url=testLoop('x-in-degraded')
print('half-open and fused again')
assertRequest(url=url,result=res,done=True,)

print('sleep FUSED_DURATION')
time.sleep(FUSED_DURATION + MEAN_ERROR)

print('mock fused recovery')
i=0
while i<10:
    res,url=mockRequest(i,success=True, action='recovery'+str(randURLPath))
    assertRequest(url=url,result=res,done=True, )
    i+=1

print('test out of LIFETIME')
totalElapsed = time.time()-start
if totalElapsed > 0 and LIFETIME-totalElapsed>0:
    print('failed before lifetime')
    i=0
    res,url=mockRequest(i,success=False,action='fail one'+str(randURLPath))
    assertRequest(url=url,result=res,done=True, )
    print('sleep to next lifetime')
    time.sleep(LIFETIME-totalElapsed)
    print('start new lifetime')
    i=0
    res,url=mockRequest(i,success=False,action='failed one'+str(randURLPath))
    assertRequest(url=url,result=res,done=True,willFails=1)
    
else:
    print('totalElapsed > LIFETIME, pass', totalElapsed)
