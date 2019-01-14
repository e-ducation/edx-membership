$(document).ready(function(){
    var time = 3;
    var odd = function () {
        if (time <= 0){
            clearInterval(timer);
            return ;
        }
        time --;        
        fmts = gettext('Return to EliteMBA in %s seconds')
        $('.wxpay-tips')[0].innerHTML = interpolate(fmts, [time]);
    }
    var timer = setInterval(odd,1000)
    setTimeout(function(){
            window.location.href = "/vip/card"
            // console.log('return')
        },3500)
})
