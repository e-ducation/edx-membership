var getQueryString = function(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i"); 
    var r = window.location.search.substr(1).match(reg); 
    if (r != null) return unescape(r[2]); return null; 
}

var getPackages = function (){
    $.ajax({
        type: "get",
        url: "/api/v1/vip/packages",
        success: function (data) {
            if(data.code == 0){
                vipListRender(data.data.results);
            }
        },
        error: function (error) {
      
        }
    });
}
var vipListRender = function(data){
    // mobile 
    var $payItem = $('.pay-item');
    var $header = $('.vip-header');
    var $number  = $('.price-number');
    var $trail  = $('.price-trail');
    var $delete = $('.delete-price');
    var $hint   = $('.price-hint');
    var $list = $('.vip-list li');
    for (var i =0,len = data.length;i <len ;i++){
        $payItem.eq(i).show();
        $payItem.eq(i).attr('data-id',data[i].id);
        $list.eq(i).attr('data-id',data[i].id);
        // mobile
        var $p =  $payItem.eq(i).find('.card-h5-message p');
        var $price = $payItem.eq(i).find('.card-h5-money span');
        $p[0].innerHTML = data[i].name;
        $p[1].innerHTML = data[i].suggested_price;
        $price[0].innerHTML = data[i].price.split('.')[0];
        $price[1].innerHTML =  '.' + data[i].price.split('.')[1];
        if(data[i].month != 1) $price[2].innerHTML = gettext('Average per month')+ (data[i].price / data[i].month).toFixed(2);
        // pc 
        $header[i].innerHTML = data[i].name;
        $number[i].innerHTML =  data[i].price.split('.')[0];
        $trail[i].innerHTML  = '.' + data[i].price.split('.')[1];
        $delete[i].innerHTML = data[i].suggested_price;
        $hint[i] = data[i].month != 1  ? gettext('Average per month')+ (data[i].price / data[i].month).toFixed(2) : '';
    }
    for (var i =3,len = data.length; i >=len ;i--){
        $list.eq(i).hide();
    }
}
// 事件控制
var eventHandler = function() {
    // 发现更多课程
    $('.find-more-professor').click(function () {
        $('.extend-professor').removeClass('hidden');
        $('.find-more-professor').hide();
    });
    // 获取设备类型
    var device = getQueryString('device');
    if(device != undefined){
        $('.global-header').hide();
        $('.my-footer').hide();
    }
    if (device != undefined){
        // app 
        // 发现课程
        $('.find-new-course').click(function(){
            if (device == 'ios'){
                window.location.href = 'eliteu://gotoFindCource';
                // alert('js find new course: ios')
            } else{
                // alert('js find new course: android')
                if (window.JsInterface) {
                    // alert('window.JsInterface')
                    JsInterface.openFindCoursePage();
                }
            }
        });
        // VIP列表
        $('.pay-item').click(function(){
            // alert(('pay-item'))
            var id = $(this).attr('data-id');
            // alert(id)
            if (device == 'ios'){
                window.location.href = 'eliteu://gotoVipPackage:id=' +id;
            }else {
                if (window.JsInterface) {
                    // alert('window.JsInterface')
                    JsInterface.openVipPage(id);
                }

            }
        });
        // 广告点击
        $('.banner-content,.add-vip-btn').click(function(){
            var id = $('.pay-item').eq(0).attr('data-id');
            if(device == 'ios'){
                window.location.href = 'eliteu://gotoVipPackage:id=' +id;
            }else{
                if (window.JsInterface) {
                    // alert('window.JsInterface')
                    JsInterface.openVipPage(id);
                }
            }
        })
    }else{
        // pc h5 
        $('.find-new-course').click(function(){
            // 跳转课程
            window.location.href = '/courses/';
        });
        $('.vip-list li').click(function(){
            var id = $(this).attr('data-id');
            window.location.href = '/vip/card?id=' + id;
        });
        $('.pay-item').click(function(){
            var id = $(this).attr('data-id');
            window.location.href = '/vip/card?id=' + id; 
        })
        $('.banner-content,.add-vip-btn').click(function(){
            var id = $('.pay-item').eq(0).attr('data-id');
            window.location.href = '/vip/card?id=' + id; 
        })
    }
}
$('document').ready(function(){
    var $payItem = $('.pay-item');
    $payItem.hide();
    $('.find-more-professor').click(function () {
        $('.extend-professor').removeClass('hidden');
        $('.find-more-professor').hide();
    });
    eventHandler();
    var device = getQueryString('device');
    // 如果设备是ios或者android 隐藏头尾
    if(device != undefined){
        $('.global-header').hide();
        $('.my-footer').hide();
    }
    getPackages();
})
