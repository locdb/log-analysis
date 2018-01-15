" only those line that contain /log..
silent! v#POST /log#d
" ..but not login 200..
silent! g#/login 200#d
" ..get rid of rubbish.
silent! %s/^\S*\zs.\{-}\ze{.*}/\t/
" Replace badly named attribute name, and...
silent! g/REFERENCE\sSELECTED/s/\<current_selected_id\>/entry_id
" ...similarly, update deprecated event identifier.
silent! %s/REFERENCE\sTARGET\sLINKED/REFERENCE TARGET SELECTED/
