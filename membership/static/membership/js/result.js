$(document).ready(function(){
    var time = 3;
    var odd = function () {
        if (time <= 0){
            clearInterval(timer);
            return ;
        }
        time --;
        $('.wxpay-tips')[0].innerHTML = StringUtils.interpolate(
            gettext('Return to EliteMBA in {second} seconds'),
            {
                secone: time
            }
        )
    }
    var timer = setInterval(odd,1000)
    setTimeout(function(){
            window.location.href = "/vip/card"
            // console.log('return')
        },3500)
})
