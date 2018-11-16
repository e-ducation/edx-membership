var vipCard = ""
//暴露付款方式以及会员价格提供到支付接口

//payWay = 0代表支付宝
//1代表微信
var payWay = 0;
var money = 0;
// vip会员信息
$.ajax({
  type: "get",
  url: "/static/membership/js/card.json",
  success: function (data) {
    var data = data.data01;

    //是会员
    if (data["isVip"] === true) {
      //会员未过期
      if (data["isTimeout"] === false) {
        var vip =
          '<ul class="vip-basic-inf">' +
          '<li class="has-vip-time">已开通<span>' + data["aredyTime"] + '</span>天 剩余<span class="has-time">' + data["hasTime"] + '</span>天</li>' +
          '<li>开通日期:<span>' + data["sTime"] + '</span></li>' +
          '<li>到期日期:<span>' + data["eTime"] + '</span></li>' +
          '</ul>';
        $(".jq-vip-message").prepend(vip);

      }
      //会员已过期
      else {
        var vip =
          '<ul class="vip-basic-inf">' +
          '<li class="has-vip-time">会员已过期<span class="has-time orange">' + data["hasTime"] + '</span>天</li>' +
          '<li>开通日期:<span>' + data["sTime"] + '</span></li>' +
          '<li>到期日期:<span>' + data["eTime"] + '</span></li>' +
          '</ul>';
        $(".jq-vip-message").prepend(vip);
      }
    }
    //不是会员
    else {
      var vip = '<p class="no-vip">开通vip会员，可免费观看英荔商学院全部课程</p>';
      $(".jq-vip-message").prepend(vip);
    }


  },
  error: function (error) {
    console.log(error);
  }
})


//选项卡
$.ajax({
  type: "get",
  url: "/api/v1/vip/packages",
  success: function (data) {

    var data = data.results;
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
          '<p class="now-money"><span>￥' + parseInt(data[i].price) + '</span>.00</p>' +
          '<p class="old-money">￥' + data[i].suggested_price + '</p>' +
          '<div class="become-vip">续费</div>' +
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
          '<p class="now-money"><span>￥' + parseInt(data[i].price) + '</span>.00</p>' +
          '<p class="old-money">￥' + data[i].suggested_price + '</p>' +
          '<div class="become-vip">续费</div>' +
          '</div>' +
          '</li>'
      }

    }

    $(".jq-card").prepend(card);

    $(".pay-box .pay-money-card").html('￥' + parseInt(data[0].price));
    money = parseInt(data[0].price);



    //手机端
    var h5Card = "";
    for (var i = 0; i < data.length; i++) {

      if (data[i].is_recommended === true) {
        h5Card += '<div>' +
          '<div class="card-h5-message">' +
          '<p>' + data[i].name + '</p>' +
          '<p>' + data[i].suggested_price + '</p>' +
          '</div>' +
          '<div class="card-h5-money"><span>' + parseInt(data[i].price) + '</span>.00</div>' +
          '<div class="h5-recommend"></div>' +
          '</div>'
      }
      else {
        h5Card += '<div>' +
          '<div class="card-h5-message">' +
          '<p>' + data[i].name + '</p>' +
          '<p>' + data[i].suggested_price + '</p>' +
          '</div>' +
          '<div class="card-h5-money"><span>' + parseInt(data[i].price) + '</span>.00</div>' +
          '</div>'
      }
    }

    $(".h5-card").prepend(h5Card);

  },
  error: function (error) {

  }
});


//pc选择会员点击事件
$(".jq-card").on('click', 'li', function () {
  var i = $(this).index();
  var left = 208;
  money = parseInt(vipCard[i].price);

  $(this).addClass("current").siblings("li").removeClass("current");

  $(".pay-box .pay-money-card").html('￥' + parseInt(vipCard[i].price));
  // 三角形移动
  $(".triangle_border_up").stop().animate({
    left: (164 + (left * i)) + 'px'
  }, 300)

});

//手机选择会员点击事件

$(".h5-card").on('click', 'div', function () {

  $(this).addClass("current").siblings("div").removeClass("current");

  var i = $(this).index();

  money = parseInt(vipCard[i].price);

  $(".h5-popup .h5-pay-money").text(money);

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

})


$(".paybtn").click(function () {
  console.log(payWay);
  console.log(money);
  console.log("支付中...");
  $(".eliteu-popup").show();
})


//弹窗关闭
$(".e-popup-colse").click(function () {
  $(".eliteu-popup").hide(300);
})

