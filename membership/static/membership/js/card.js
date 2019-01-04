var getQueryString = function(name) {
  var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i"); 
  var r = window.location.search.substr(1).match(reg); 
  if (r != null) return unescape(r[2]); return null; 
}
var vipCard = ""
//暴露付款方式以及会员价格提供到支付接口

//payWay = 0代表支付宝
//1代表微信
var payWay = 0;
var money = 0;
//订单id
var orderId;
// vip会员信息

//续费or开通
// var isBtnVip = '<div class="become-vip">开通</div>';
var isBtnVip = '<div class="become-vip">' + gettext('Open membership') + '</div>'

//是否是手机
var phone = isMoblie();
//不是会员
var novip = '<p class="no-vip">' + gettext('Become a VIP member and watch all EliteMBA courses for free') + '</p>';

$.ajax({
  type: "get",
  url: "/api/v1/vip/info",
  success: function (res) {

    var res = res.data;
    if (res === null) {
      $(".jq-vip-message").prepend(novip);
    }
    else {
      var data = {
        isVip: res.status,
        isTimeout: moment(res.expired_at) < moment(),
        aredyTime: res.opened,
        hasTime: res.remain,
        expiredTime:res.expired,
        sTime: moment(res.start_at).format(gettext("YYYY-MM-DD")),
        eTime: moment(res.expired_at).format(gettext("YYYY-MM-DD"))
      }

      if (res.start_at != undefined) {
        //会员未过期
        if (data["isVip"] === true) {

          if (phone) {
            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">' + gettext("Membership opened") + '<span>' + data["aredyTime"] + '</span>' + gettext("day") + gettext("Remaining days") + '<span class="has-time">' + data["hasTime"] + '</span>' + gettext("day") + '</li>' +
              '<li>' + gettext("Duration:") + '<span>' + data["sTime"] + ' ~ ' + data["eTime"] + '</span></li>' +
              '</ul>';
          }
          else {

            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">' + gettext("Membership opened") + '<span>' + data["aredyTime"] + '</span>' + gettext("day") + gettext("Remaining days") + '<span class="has-time">' + data["hasTime"] + '</span>' + gettext("day") + '</li>' +
              '<li>' + gettext("Opened on:") + '<span>' + data["sTime"] + '</span></li>' +
              '<li>' + gettext("Expire on:") + '<span>' + data["eTime"] + '</span></li>' +
              '</ul>';
          }

          $(".jq-vip-message").prepend(vip);

        }
        //会员已过期
        else {

          if (phone) {

            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">' + gettext("Membership opened") + '<span>' + data["aredyTime"] + '</span>' + gettext("day") + gettext("Remaining days") + '<span class="has-time">' + data["hasTime"] + '</span>' + gettext("day") + '</li>' +
              '<li>' + gettext("Duration:") + '<span>' + data["sTime"] + ' ~ ' + data["eTime"] + '</span></li>' +
              '</ul>';
          }
          else {
            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">' + gettext("Membership expired") + '<span class="has-time orange">' + data["expiredTime"] + '</span>' + gettext("day") + '</li>' +
              '<li>' + gettext("Opened on:") + '<span>' + data["sTime"] + '</span></li>' +
              '<li>' + gettext("Expire on:") + '<span>' + data["eTime"] + '</span></li>' +
              '</ul>';
          }
          $(".jq-vip-message").prepend(vip);

        }

        isBtnVip = '<div class="become-vip">' + gettext('Renew') + '</div>';
      }
      //不是会员
      else {
        $(".jq-vip-message").prepend(novip);
      }
    }

  },
  error: function (error) {
    //获取出错的情况下
    isBtnVip = '<div class="become-vip">' + gettext("Open membership") + '</div>';
    if (error.status === 403) {
      $(".jq-vip-message").prepend(novip);
    }
    else {
      $(".jq-vip-message").prepend(novip);
    }

  }
})


//选项卡
$.ajax({
  type: "get",
  url: "/api/v1/vip/packages",
  success: function (data) {

    var data = data.data.results;
    var card = '';
    vipCard = data;
    var target = getQueryString('id');
    for (var i = 0; i < data.length; i++) {

      //PC端
      var d1;
      if (target !=undefined && target == data[i].id){
        d1 = '<li class="current" data-id="pay' + data[i].id + '">'
      }else if (target ==undefined && i == 0) {
        d1 = '<li class="current" data-id="pay' + data[i].id + '">'
      } else {
        d1 = '<li data-id="pay' + data[i].id + '">'
      }

      if (data[i].is_recommended === true) {
        card += d1 +
          '<div class="vip-card-header">' +
          '<p>' + data[i].name + '</p>' +
          '</div>' +
          '<div class="vip-card-body">' +
          '<p class="now-money"><span>￥' + data[i].price.split(".")[0] + '</span>.' + data[i].price.split(".")[1] + '</p>' +
          '<p class="old-money">￥' + data[i].suggested_price + '</p>' +
          isBtnVip +
          '</div>' +
          '<div class="recommend"></div>' +
          '</li>'
      }
      else {
        card += d1 +
          '<div class="vip-card-header">' +
          '<p>' + data[i].name + '</p>' +
          '</div>' +
          '<div class="vip-card-body">' +
          '<p class="now-money"><span>￥' + data[i].price.split(".")[0] + '</span>.' + data[i].price.split(".")[1] + '</p>' +
          '<p class="old-money">￥' + data[i].suggested_price + '</p>' +
          isBtnVip +
          '</div>' +
          '</li>'
      }

    }

    $(".jq-card").prepend(card);

    
    money = data[0].price;
   

    //手机端
    var h5Card = "";
    for (var i = 0; i < data.length; i++) {

      if (data[i].is_recommended === true) {
        h5Card += '<div>' +
          '<div class="card-h5-message">' +
          '<p>' + data[i].name + '</p>' +
          '<p>' + data[i].suggested_price + '</p>' +
          '</div>' +
          '<div class="card-h5-money"><span>' + data[i].price.split(".")[0] + '</span>.' + data[i].price.split(".")[1] + '</div>' +
          '<div class="h5-recommend"></div>' +
          '</div>'
      }
      else {
        h5Card += '<div>' +
          '<div class="card-h5-message">' +
          '<p>' + data[i].name + '</p>' +
          '<p>' + data[i].suggested_price + '</p>' +
          '</div>' +
          '<div class="card-h5-money"><span>' + data[i].price.split(".")[0] + '</span>.' + data[i].price.split(".")[1] + '</div>' +
          '</div>'
      }
    }
    $(".h5-card").prepend(h5Card);

    // target init 
    var _index = 0;
    if (target != undefined){
      for(var i = 0,len =data.length;i <len;i++){
        if (data[i].id == target){
          _index = i
        }
      }
    }
    orderId = data[_index].id;
    // 初始化信息
    $(".vip-name-pay").text(data[_index].name)
    $(".pay-box .pay-money-card").html('￥' + data[_index].price.split(".")[0]);
    $(".pay-box .pay-money-card01").html('.' + data[_index].price.split(".")[1]);
  },
  error: function (error) {

  }
});


//pc选择会员点击事件
$(".jq-card").on('click', 'li', function () {
  var i = $(this).index();
  var left = 208;
  money = vipCard[i].price;

  orderId = vipCard[i].id;


  $(this).addClass("current").siblings("li").removeClass("current");

  $(".pay-box .pay-money-card").html('￥' + vipCard[i].price.split(".")[0]);
  $(".pay-box .pay-money-card01").html('.' + vipCard[i].price.split(".")[1]);

  $(".vip-name-pay").text(vipCard[i].name);

  // 三角形移动
  $(".triangle_border_up").stop().animate({
    left: (164 + (left * i)) + 'px'
  }, 300)

});

//手机选择会员点击事件

$(".h5-card").on('click', 'div', function () {

  $(this).addClass("current").siblings("div").removeClass("current");

  var i = $(this).index();

  money = vipCard[i].price;

  orderId = vipCard[i].id;

  $(".h5-popup .h5-pay-money").text(money.split(".")[0]);
  $(".h5-popup .h5-pay-money01").text('.' + money.split(".")[1]);

  $(".h5-popup").show();

})

$(".h5-popup").click(function () {
  $(".h5-popup").hide();
})


$('.popup-pay>div').click(function (e) {
  if (e.stopPropagation()) {
    e.stopPropagation();
  }
  else {
    e.cancelBubble = true;
  }
  payWay = $(this).index();

  $(this).children(".round").css({ background: "url('../static/membership/images/Group.png') no-repeat center", backgroundSize: '16px' });
  $(this).siblings("div").children(".round").css({ background: "url('../static/membership/images/Normal.png') no-repeat center", backgroundSize: '16px' })
})


//选择支付方式
$(".pay li").click(function () {

  payWay = $(this).index();

  $(this).addClass("current").siblings("li").removeClass("current");

  $(this).prepend('<img src="../static/membership/images/Group.png" alt="" class="imgCurrent"></img>').siblings("li").children('img').remove();

})

$(".paybtn").click(function () {
  if(!checkLogin()){
    return;
  }
  if (payWay == 0) {
    aliPayer(orderId);
  } else {
    wxPayer(orderId);
  }

  $(".eliteu-popup").show();

})

$(".h5btn-pay").click(function () {
  if(!checkLogin()){
    return;
  }
  if (payWay == 0) {
    aliH5Payer(orderId);
  } else {
    wxH5Payer(orderId);
  }

})


function checkLogin(){
  var vip_status = $('#vip_status').html();
  var card_url = $('#card_url').attr('href');
  if (vip_status == 'False'){
    window.location.href = card_url;
    return false;
  }
  return true;
}
// 弹窗关闭
$('.e-popup-colse,.popup-btnGrounp a:nth-of-type(1)').click(function(){
  $(".eliteu-popup").hide();
});
// 支付完成
$('.popup-btnGrounp a:nth-of-type(2),.popup-btnGrounp a:nth-of-type(3)').click(function(){
  window.location.reload();
})


