$(document).ready(function(){
    $.ajax({
        type: 'GET',
        dataType: 'json',
        url: '/autoapi',
        success: function(data){
            var availableTagsh = data.namelist;
            $("#autoc").autocomplete({
                source: availableTagsh
            });
        }
    })
});