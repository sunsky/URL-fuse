local lib={}
function lib:dump(o)
   if type(o) == 'table' then
      local s = '{ '
      for k,v in pairs(o) do
         if type(k) ~= 'number' then k = '"'..k..'"' end
         s = s .. '['..k..'] = ' .. lib:dump(v) .. ','
      end
      return s .. '} '
   else
      return tostring(o)
   end
end
function lib:json(o)
	local json = require('cjson')
	return json.encode(o)
end
function lib:json2obj(o)
	local json = require('cjson')
	return json.decode(o)
end
return lib
