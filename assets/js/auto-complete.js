$(function(){
    var cache = {};
    var time_check = {};
    $("#autoc").autocomplete({
        minLength: 1,
        source: function(request, response){
            var term = request.term;
            if (term in cache){
                if (new Data().getTime()-time_check[term]<3600000){
                    ret_list = [];
                    if (cache[term].length > 20){
                        for (var i = 0; i < 20; i++){
                            ret_list[ret_list.length] = cache[term][i];
                        }
                    } else{
                        ret_list=cache[term];
                    }
                    response(ret_list);
                    return;
                }
            }

            $.getJSON("/autoapi", request, function(data, status, xhr){
                if (data.ready){
                    cache[term] = data.tags;
                    time_check[term] = new Date().getTime();
                    ret_list=[];
                    if (cache[term].length > 20){
                        for (var i = 0; i < 20; i++){
                            ret_list[ret_list.length] = cache[term][i];
                        }
                    } else{
                        ret_list=cache[term];
                    }
                    response(ret_list);
                }
            });
        }
    });
});

//$(function(){
//    var cache = {};
//    $('#autoc').autocomplete({
//        minLength: 1,
//        source: function(request, response){
//            var term = request.term;
//            if (term in cache){
//                response(cache[term]);
//                return;
//            }
//
//            $.getJSON("/autoapi", request, function(data, status, xhr){
//                cache[term] = data.namelist;
//                response(cache);
//            });
//        }
//    });
//});

//$(document).ready(function(){
//    $.ajax({
//        type: 'POST',
//        dataType: 'json',
//        url: '/autoapi',
//        success: function(data){
//            var availableTagsh = data.namelist;
//            $("#autoc").autocomplete({
//                source: availableTagsh
//            });
//        }
//    })
//});