window.onload = function(){
    var time = 3;
    var odd = function () {
        if (time <= 0){
            clearInterval(timer);
            return ;
        }
        time --;
        $('.wxpay-tips')[0].innerHTML = time + gettext('秒后返回英荔商学院');
    }
    var timer = setInterval(odd,1000)
    setTimeout(function(){
            window.location.href = "/vip/card"
            // console.log('return')
        },3500)
}

var checkStatus = function () {
    this.start = function(cb,id) {
        this.flag = true;
        var that = this;
        this.auto = setInterval(function(){
            // if this.flag == true
            if (that.flag){
                $.ajax({
                    url: '/api/v1/vip/order/'+ id,
                    xhrFields: { withCredentials: true},
                    success: function(res){
                        console.log('success',res);
                        // that.flag = false;
                        if (res.data.status == 2 && that.flag){
                            that.stop()
                            cb && cb();
                        }
                    },
                    error: function(err){
                        // that.stop();
                        // that.flag = false;
                        console.log('error',err)
                    }
                })
            } else {
                console.log('checkout order')
            }
        },1000)
    }
    this.stop = function() {
        if (this.auto) {
            this.flag = false;
            clearInterval(this.auto);
        }
    }
}
var aliPayer = function(id) {
    $.ajax({
        url: '/api/v1/vip/pay/alipay/paying/?package_id='+id,
        xhrFields: { withCredentials: true},
        success: function(res){
            if (res.code == 0){
                var tempwindow = window.open("",'_blank');
                tempwindow.location = res.data.alipay_url;
                // var checker =  new checkStatus()
                // checker.start(function(){
                //     alert('支付成功')
                //     $(".eliteu-popup").hide(300);
                // },res.data.order_id);
            }
        },
        error: function(){
            console.log('error')
        },
        async: false
    })
}
var wxPayer = function(id){
    $.ajax({
        url: '/api/v1/vip/pay/wechat/paying/?package_id='+id,
        xhrFields: { withCredentials: true},
        success: function(res){
            if (res.code == 0) {
                var tempwindow = window.open("",'_blank');
                tempwindow.location = res.data.href_url;
            }
        },
        error: function(){
            console.log('error')
        },
        async: false // 防止拦截
    }) 
}

var isMoblie = function(){
    return navigator.userAgent.match(/(iPhone|iPod|Android|ios|iPad)/i);
}
