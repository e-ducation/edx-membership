


var checkStatus = function () {
    this.start = function(cb,id) {
        this.flag = true;
        var that = this;
        this.auto = setInterval(function(){
            // if this.flag == true
            console.log('checking',that.flag)
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
            console.log('success')
            if (res.code == 0){
                var tempwindow = window.open("",'_blank');
                tempwindow.location = res.data.alipay_url;
                var checker =  new checkStatus()
                checker.start(function(){
                    alert('支付成功')
                    // $('#paying').hide();
                    // $('#result').show();
                    // window.location.href = "/vip/pay/result"
                    $(".eliteu-popup").hide(300);
                    // window.location.reload();
                    setTimeout(function(){
                        // window.location.href = "/vip/card"
                    },3000)
                },res.data.order_id);
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
            console.log('success',res);
            if (res.code == 0) {
                var tempwindow = window.open("",'_blank');
                tempwindow.location = res.data.href_url;
                // window.location.href = res.href_url;
            }
            // if (res.code == 0){
            //     var tempwindow = window.open("",'_blank');
            //     tempwindow.location = res.data.alipay_url;
            // }
            // window.location.href = res.href_url;
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
