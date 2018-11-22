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
var isBtnVip = '<div class="become-vip">开通</div>';

//是否是手机
var phone = isMoblie();
//不是会员
var novip = '<p class="no-vip">开通vip会员，可免费观看英荔商学院全部课程</p>';

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
        sTime: moment(res.start_at).format("YYYY年MM月DD日"),
        eTime: moment(res.expired_at).format("YYYY年MM月DD日")
      }

      if (res.start_at != undefined) {
        //会员未过期
        if (data["isVip"] === true) {

          if (phone) {
            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">已开通<span>' + data["aredyTime"] + '</span>天 剩余<span class="has-time">' + data["hasTime"] + '</span>天</li>' +
              '<li>日期: <span>' + data["sTime"] + '</span></li>' +
              '<li>日期: <span>' + data["eTime"] + '</span></li>' +
              '</ul>';
          }
          else {

            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">已开通<span>' + data["aredyTime"] + '</span>天 剩余<span class="has-time">' + data["hasTime"] + '</span>天</li>' +
              '<li>开通日期: <span>' + data["sTime"] + '</span></li>' +
              '<li>到期日期: <span>' + data["eTime"] + '</span></li>' +
              '</ul>';
          }

          $(".jq-vip-message").prepend(vip);

        }
        //会员已过期
        else {

          if (phone) {

            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">会员已过期<span class="has-time orange">' + data["hasTime"] + '</span>天</li>' +
              '<li>日期: <span>' + data["sTime"] + '</span></li>' +
              '<li>日期: <span>' + data["eTime"] + '</span></li>' +
              '</ul>';
          }
          else {
            var vip =
              '<ul class="vip-basic-inf">' +
              '<li class="has-vip-time">会员已过期<span class="has-time orange">' + data["hasTime"] + '</span>天</li>' +
              '<li>开通日期: <span>' + data["sTime"] + '</span></li>' +
              '<li>到期日期: <span>' + data["eTime"] + '</span></li>' +
              '</ul>';
          }
          $(".jq-vip-message").prepend(vip);

        }

        isBtnVip = '<div class="become-vip">续费</div>';
      }
      //不是会员
      else {
        $(".jq-vip-message").prepend(novip);
      }
    }

  },
  error: function (error) {
    //获取出错的情况下
    isBtnVip = '<div class="become-vip">开通</div>';
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

    for (var i = 0; i < data.length; i++) {

      //PC端
      var d1;
      if (i == 0) {
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

    $(".pay-box .pay-money-card").html('￥' + data[0].price.split(".")[0]);
    $(".pay-box .pay-money-card01").html('.' + data[0].price.split(".")[1]);
    money = data[0].price;
    $(".vip-name-pay").text(data[0].name)

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

    orderId = data[0].id;

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
    aliPayer(orderId);
  } else {
    wxPayer(orderId);
  }

})

//弹窗关闭
function hide(item) {

  $(item).click(function () {
    $(".eliteu-popup").hide();
  });

}
function checkLogin(){
  var vip_status = $('#vip_status').html();
  var card_url = $('#card_url').attr('href');
  if (vip_status == 'False'){
    window.location.href = card_url;
    return false;
  }
  return true;
}
hide(".e-popup-colse");
hide(".popup-btnGrounp a:nth-of-type(1)");
hide(".popup-btnGrounp a:nth-of-type(2)");



