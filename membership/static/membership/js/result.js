$(document).ready(function(){
    var time = 3;
    var odd = function () {
        if (time <= 0){
            clearInterval(timer);
            return ;
        }
        time --;
        $('.wxpay-tips')[0].innerHTML = time + gettext('Return to EliteMBA in _ seconds');
    }
    var timer = setInterval(odd,1000)
    setTimeout(function(){
            window.location.href = "/vip/card"
            // console.log('return')
        },3500)
})
