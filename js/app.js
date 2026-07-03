/* ============================================================
   中国人情世故情商测评 - 主程序逻辑
   计分引擎 + 分页答题 + 报告生成
   ============================================================ */

var App = {
  // 当前状态
  state: {
    currentPage: 0,            // 当前页码（0-based）
    questionsPerPage: 6,       // 每页题数
    answers: {},               // { questionId: optionIndex }
    screen: "home"             // home | test | result
  },

  // ============ 初始化 ============
  init: function () {
    this.initTheme();
    this.bindEvents();
    this.showScreen("home");
  },

  // ============ 深色模式初始化 ============
  initTheme: function () {
    var saved = localStorage.getItem("eq-test-theme");
    if (saved === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      var btn = document.getElementById("theme-toggle");
      if (btn) btn.textContent = "☀️";
    }
  },

  // ============ 事件绑定 ============
  bindEvents: function () {
    var self = this;

    // 首页开始按钮
    document.getElementById("btn-start").addEventListener("click", function () {
      self.startTest();
    });

    // 下一页
    document.getElementById("btn-next").addEventListener("click", function () {
      self.nextPage();
    });

    // 上一页
    document.getElementById("btn-prev").addEventListener("click", function () {
      self.prevPage();
    });

    // 重新测试
    document.getElementById("btn-retry").addEventListener("click", function () {
      self.startTest();
    });

    // 返回首页
    document.getElementById("btn-home").addEventListener("click", function () {
      self.showScreen("home");
    });

    // 深色模式切换
    var themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        self.toggleTheme();
      });
    }
  },

  // ============ 屏幕切换 ============
  showScreen: function (screen) {
    this.state.screen = screen;
    document.getElementById("screen-home").classList.add("hidden");
    document.getElementById("screen-test").classList.add("hidden");
    document.getElementById("screen-result").classList.add("hidden");
    document.getElementById("screen-" + screen).classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  },

  // ============ 深色模式切换 ============
  toggleTheme: function () {
    var html = document.documentElement;
    var btn = document.getElementById("theme-toggle");
    if (html.getAttribute("data-theme") === "dark") {
      html.removeAttribute("data-theme");
      if (btn) btn.textContent = "🌙";
      localStorage.setItem("eq-test-theme", "light");
    } else {
      html.setAttribute("data-theme", "dark");
      if (btn) btn.textContent = "☀️";
      localStorage.setItem("eq-test-theme", "dark");
    }
  },

  // ============ 开始测评 ============
  startTest: function () {
    this.state.currentPage = 0;
    this.state.answers = {};
    this.showScreen("test");
    this.renderPage();
  },

  // ============ 总页数 ============
  totalPages: function () {
    return Math.ceil(QUESTIONS.length / this.state.questionsPerPage);
  },

  // ============ 渲染当前页题目 ============
  renderPage: function () {
    var page = this.state.currentPage;
    var perPage = this.state.questionsPerPage;
    var start = page * perPage;
    var end = Math.min(start + perPage, QUESTIONS.length);
    var total = this.totalPages();

    // 进度条
    var progressEl = document.getElementById("test-progress");
    var answered = Object.keys(this.state.answers).length;
    var progressPct = Math.round((answered / QUESTIONS.length) * 100);
    progressEl.innerHTML =
      '<div class="progress-wrap">' +
      '<div class="progress-text"><span>总进度</span><span>' + answered + ' / ' + QUESTIONS.length + ' 题已答</span></div>' +
      '<div class="progress-bar"><div class="progress-fill" style="width:' + progressPct + '%"></div></div>' +
      '</div>' +
      '<span class="category-badge">第 ' + (page + 1) + ' / ' + total + ' 页</span>';

    // 题目列表
    var container = document.getElementById("questions-container");
    var html = "";
    for (var i = start; i < end; i++) {
      html += this.renderQuestion(QUESTIONS[i], i);
    }
    container.innerHTML = html;

    // 为每个选项绑定点击事件
    for (var j = start; j < end; j++) {
      this.bindOptionEvents(QUESTIONS[j].id);
    }

    // 导航按钮
    this.updateNavButtons();
  },

  // ============ 渲染单题 ============
  renderQuestion: function (q, index) {
    var letters = ["A", "B", "C", "D"];
    var selectedIdx = this.state.answers[q.id];
    var html = '<div class="question-card">';
    html += '<div class="q-number">第 ' + (index + 1) + ' 题 <span style="color:var(--text-muted)">| ' + q.category + '</span></div>';
    html += '<div class="q-scenario">' + this.escapeHtml(q.scenario) + '</div>';
    html += '<div class="q-text">' + this.escapeHtml(q.question) + '</div>';
    html += '<div class="options-list" id="options-' + q.id + '">';
    for (var i = 0; i < q.options.length; i++) {
      var opt = q.options[i];
      var selClass = (selectedIdx === i) ? " selected" : "";
      html +=
        '<button class="option-btn' + selClass + '" data-qid="' + q.id + '" data-oidx="' + i + '">' +
        '<span class="option-letter">' + letters[i] + '</span>' +
        '<span class="option-content">' + this.escapeHtml(opt.text) + '</span>' +
        '</button>';
    }
    html += '</div></div>';
    return html;
  },

  // ============ HTML转义 ============
  escapeHtml: function (str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  },

  // ============ 绑定选项事件 ============
  bindOptionEvents: function (qid) {
    var self = this;
    var container = document.getElementById("options-" + qid);
    if (!container) return;
    var buttons = container.querySelectorAll(".option-btn");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function () {
        var oidx = parseInt(this.getAttribute("data-oidx"));
        self.selectOption(qid, oidx);
      });
    }
  },

  // ============ 选择答案 ============
  selectOption: function (qid, oidx) {
    this.state.answers[qid] = oidx;

    // 更新UI
    var container = document.getElementById("options-" + qid);
    if (!container) return;
    var buttons = container.querySelectorAll(".option-btn");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].classList.remove("selected");
    }
    buttons[oidx].classList.add("selected");

    // 更新进度条
    var answered = Object.keys(this.state.answers).length;
    var progressPct = Math.round((answered / QUESTIONS.length) * 100);
    var fillEl = document.querySelector(".progress-fill");
    if (fillEl) fillEl.style.width = progressPct + "%";
    var textEl = document.querySelector(".progress-text span:last-child");
    if (textEl) textEl.textContent = answered + " / " + QUESTIONS.length + " 题已答";

    this.updateNavButtons();
  },

  // ============ 更新导航按钮 ============
  updateNavButtons: function () {
    var page = this.state.currentPage;
    var total = this.totalPages();
    var isLast = page === total - 1;
    var answeredAll = Object.keys(this.state.answers).length === QUESTIONS.length;
    var perPage = this.state.questionsPerPage;
    var start = page * perPage;
    var end = Math.min(start + perPage, QUESTIONS.length);
    var pageAnswered = true;
    for (var i = start; i < end; i++) {
      if (this.state.answers[QUESTIONS[i].id] === undefined) {
        pageAnswered = false;
        break;
      }
    }

    var prevBtn = document.getElementById("btn-prev");
    var nextBtn = document.getElementById("btn-next");

    prevBtn.classList.toggle("hidden", page === 0);

    if (isLast) {
      nextBtn.textContent = "查看测评结果";
      nextBtn.className = "btn btn-accent";
      nextBtn.disabled = !answeredAll;
    } else {
      nextBtn.textContent = "下一页";
      nextBtn.className = "btn btn-primary";
      nextBtn.disabled = false;
    }
  },

  // ============ 下一页 ============
  nextPage: function () {
    var total = this.totalPages();
    if (this.state.currentPage === total - 1) {
      // 最后一页 -> 提交结果
      if (Object.keys(this.state.answers).length < QUESTIONS.length) {
        var un = QUESTIONS.length - Object.keys(this.state.answers).length;
        alert("还有 " + un + " 道题没有作答，请全部完成后查看结果。");
        return;
      }
      this.showResult();
      return;
    }
    this.state.currentPage++;
    this.renderPage();
    window.scrollTo({ top: 0, behavior: "smooth" });
  },

  // ============ 上一页 ============
  prevPage: function () {
    if (this.state.currentPage > 0) {
      this.state.currentPage--;
      this.renderPage();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  },

  // ================================================================
  //  计分引擎
  //  基于 EQ-Bench 精细化六维度打分模型
  // ================================================================

  calculateScores: function () {
    var dimRaw = {};       // { dimName: totalScore }
    var dimCount = {};     // { dimName: questionCount }
    var maxPerQ = 4;       // 每题最高4分

    // 初始化维度
    var dims = ["人情分寸", "察言观色", "情绪自控", "应酬处事", "冲突化解", "人际边界"];
    for (var d = 0; d < dims.length; d++) {
      dimRaw[dims[d]] = 0;
      dimCount[dims[d]] = 0;
    }

    // 遍历所有题目
    for (var i = 0; i < QUESTIONS.length; i++) {
      var q = QUESTIONS[i];
      var selected = this.state.answers[q.id];
      if (selected === undefined) continue;

      var rawScore = q.options[selected].score;

      for (var j = 0; j < q.dimensions.length; j++) {
        var dim = q.dimensions[j];
        dimRaw[dim] += rawScore;
        dimCount[dim] += 1;
      }
    }

    // 计算百分比分数
    var dimPercent = {};
    var totalRaw = 0;
    var totalMax = 0;

    for (var k = 0; k < dims.length; k++) {
      var dn = dims[k];
      var maxPossible = dimCount[dn] * maxPerQ;
      dimPercent[dn] = maxPossible > 0 ? Math.round((dimRaw[dn] / maxPossible) * 100) : 0;
      totalRaw += dimRaw[dn];
      totalMax += maxPossible;
    }

    var overallPercent = totalMax > 0 ? Math.round((totalRaw / totalMax) * 100) : 0;

    return {
      raw: dimRaw,
      count: dimCount,
      percent: dimPercent,
      overall: overallPercent
    };
  },

  // ============ 确定评级 ============
  determineRating: function (scores) {
    var overall = scores.overall;
    var pct = scores.percent;
    var boundary = pct["人际边界"];
    var conflict = pct["冲突化解"];
    var cues = pct["察言观色"];
    var measure = pct["人情分寸"];

    // 讨好型老好人：整体不差但人际边界和冲突化解明显偏低
    if (overall >= 55 && boundary < 55 && conflict < 55) {
      return "pleaser";
    }

    // 人情通透高手：整体高分且各维度均衡
    if (overall >= 85) {
      return "master";
    }

    // 直性子不懂人情：整体低分
    if (overall < 60) {
      return "straight";
    }

    // 处事稳妥普通人：中间地带
    return "average";
  },

  // ============ 获取短板维度（最低2个） ============
  getWeakDimensions: function (scores) {
    var pct = scores.percent;
    var entries = [];
    for (var dim in pct) {
      if (pct.hasOwnProperty(dim)) {
        entries.push({ dim: dim, score: pct[dim] });
      }
    }
    entries.sort(function (a, b) { return a.score - b.score; });
    return entries.slice(0, 2);
  },

  // ============ 获取强项维度（最高2个） ============
  getStrongDimensions: function (scores) {
    var pct = scores.percent;
    var entries = [];
    for (var dim in pct) {
      if (pct.hasOwnProperty(dim)) {
        entries.push({ dim: dim, score: pct[dim] });
      }
    }
    entries.sort(function (a, b) { return b.score - a.score; });
    return entries.slice(0, 2);
  },

  // ============ 获取话术建议 ============
  getScripts: function (weakDims) {
    var scripts = [];
    for (var i = 0; i < weakDims.length; i++) {
      var dimName = weakDims[i].dim;
      var dimScripts = SOCIAL_SCRIPTS[dimName];
      if (dimScripts) {
        for (var j = 0; j < dimScripts.length; j++) {
          scripts.push({
            dimension: dimName,
            scenario: dimScripts[j].scenario,
            script: dimScripts[j].script
          });
        }
      }
    }
    return scripts;
  },

  // ============ 绘制环形分数 ============
  drawScoreRing: function (containerId, percentage) {
    var container = document.getElementById(containerId);
    if (!container) return;
    var size = 120;
    var stroke = 10;
    var radius = (size - stroke) / 2;
    var circumference = 2 * Math.PI * radius;
    var offset = circumference - (percentage / 100) * circumference;
    var color;
    if (percentage >= 80) color = "#2D8B4E";
    else if (percentage >= 60) color = "#D69A2E";
    else color = "#C53030";

    container.innerHTML =
      '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '">' +
      '<circle cx="' + (size / 2) + '" cy="' + (size / 2) + '" r="' + radius + '" fill="none" stroke="#E8D5C4" stroke-width="' + stroke + '"/>' +
      '<circle cx="' + (size / 2) + '" cy="' + (size / 2) + '" r="' + radius + '" fill="none" stroke="' + color + '" stroke-width="' + stroke + '" stroke-linecap="round" stroke-dasharray="' + circumference + '" stroke-dashoffset="' + offset + '" style="transition: stroke-dashoffset 1.5s ease;"/>' +
      '</svg>' +
      '<div class="score-value">' + percentage + '<span class="score-unit">分</span></div>';
  },

  // ============ 生成报告 ============
  showResult: function () {
    var scores = this.calculateScores();
    var ratingId = this.determineRating(scores);
    var rating = null;
    for (var r = 0; r < RATING_SYSTEM.length; r++) {
      if (RATING_SYSTEM[r].id === ratingId) { rating = RATING_SYSTEM[r]; break; }
    }
    if (!rating) rating = RATING_SYSTEM[3];

    var weakDims = this.getWeakDimensions(scores);
    var strongDims = this.getStrongDimensions(scores);
    var scripts = this.getScripts(weakDims);

    this.showScreen("result");
    this.renderResult(scores, rating, weakDims, strongDims, scripts);
  },

  // ============ 渲染结果 ============
  renderResult: function (scores, rating, weakDims, strongDims, scripts) {
    // 评级头部
    document.getElementById("rating-emoji").textContent = rating.emoji;
    document.getElementById("rating-name").textContent = rating.name;
    document.getElementById("rating-desc").textContent = rating.description;

    // 综合分数环形图
    var self = this;
    setTimeout(function () {
      self.drawScoreRing("overall-score-ring", scores.overall);
    }, 100);

    // 维度分数条
    var dims = ["人情分寸", "察言观色", "情绪自控", "应酬处事", "冲突化解", "人际边界"];
    var dimsHtml = "";
    for (var i = 0; i < dims.length; i++) {
      var dn = dims[i];
      var sp = scores.percent[dn];
      var levelClass = sp >= 75 ? "high" : (sp >= 50 ? "medium" : "low");
      var def = DIMENSION_DEFINITIONS[dn];
      dimsHtml +=
        '<div class="dim-score-item">' +
        '<span class="dim-score-label">' + def.icon + ' ' + dn + '</span>' +
        '<div class="dim-score-bar-wrap"><div class="dim-score-bar-fill ' + levelClass + '" style="width:' + sp + '%"></div></div>' +
        '<span class="dim-score-value">' + sp + '%</span>' +
        '</div>';
    }
    document.getElementById("dimension-scores").innerHTML = dimsHtml;

    // 强项分析
    var strengthsHtml = "";
    for (var s = 0; s < strongDims.length; s++) {
      var sd = strongDims[s];
      var sdef = DIMENSION_DEFINITIONS[sd.dim];
      strengthsHtml += '<div class="analysis-item"><strong>' + sdef.icon + ' ' + sd.dim + '（' + sd.score + '%）：</strong>' + sdef.highText + '</div>';
    }
    document.getElementById("strengths-list").innerHTML = strengthsHtml;

    // 短板分析
    var weakHtml = "";
    for (var w = 0; w < weakDims.length; w++) {
      var wd = weakDims[w];
      var wdef = DIMENSION_DEFINITIONS[wd.dim];
      weakHtml += '<div class="analysis-item"><strong>' + wdef.icon + ' ' + wd.dim + '（' + wd.score + '%）：</strong>' + wdef.lowText + '</div>';
    }
    document.getElementById("weakness-list").innerHTML = weakHtml;

    // 评级提示
    if (rating.warning) {
      document.getElementById("warning-box").classList.remove("hidden");
      document.getElementById("warning-text").textContent = rating.warningText;
    } else {
      document.getElementById("warning-box").classList.add("hidden");
    }

    // 话术建议
    var scriptsHtml = "";
    for (var c = 0; c < scripts.length; c++) {
      var sc = scripts[c];
      scriptsHtml +=
        '<div class="script-card">' +
        '<div class="script-scenario">[' + sc.dimension + '] ' + this.escapeHtml(sc.scenario) + '</div>' +
        '<div class="script-content">' + this.escapeHtml(sc.script) + '</div>' +
        '</div>';
    }
    document.getElementById("scripts-list").innerHTML = scriptsHtml;

    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
};

// ============ 页面加载完成后初始化 ============
document.addEventListener("DOMContentLoaded", function () {
  App.init();
});
