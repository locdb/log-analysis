" only those line that contain /log..
v#POST /log#d
" ..but not login 200..
g#/login 200#d
" ..get rid of rubbish
%s/^\S*\zs.\{-}\ze{.*}/\t/
" correct misplaced attribute name
g/REFERENCE\sSELECTED/s/\<current_selected_id\>/entry_id
