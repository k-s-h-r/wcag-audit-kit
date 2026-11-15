# 人による確認の引き継ぎ

ここにある項目は未確認です。引き継ぎを記録しても検証完了・適合にはなりません。
このファイルは依頼内容の出力であり、外部への送信や担当者への連絡は行っていません。

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--initial--desktop--1.4.4
対象: http://127.0.0.1:4330/ / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--initial--desktop/page.png, evidence/eed089bd8f88--initial--desktop/inventory.json, evidence/eed089bd8f88--initial--desktop/dom.html, evidence/eed089bd8f88--initial--desktop/accessibility-tree.json, evidence/eed089bd8f88--initial--desktop/actions.json, evidence/eed089bd8f88--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / initial / desktop

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--initial--desktop/page.png, evidence/eed089bd8f88--initial--desktop/inventory.json, evidence/eed089bd8f88--initial--desktop/dom.html, evidence/eed089bd8f88--initial--desktop/accessibility-tree.json, evidence/eed089bd8f88--initial--desktop/actions.json, evidence/eed089bd8f88--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--initial--desktop--1.4.4--8163a1a934fe.json](assessments/eed089bd8f88--initial--desktop--1.4.4--8163a1a934fe.json)

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--anonymous--desktop--1.4.4
対象: http://127.0.0.1:4330/ / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--anonymous--desktop/page.png, evidence/eed089bd8f88--anonymous--desktop/inventory.json, evidence/eed089bd8f88--anonymous--desktop/dom.html, evidence/eed089bd8f88--anonymous--desktop/accessibility-tree.json, evidence/eed089bd8f88--anonymous--desktop/actions.json, evidence/eed089bd8f88--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / anonymous / desktop

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--anonymous--desktop/page.png, evidence/eed089bd8f88--anonymous--desktop/inventory.json, evidence/eed089bd8f88--anonymous--desktop/dom.html, evidence/eed089bd8f88--anonymous--desktop/accessibility-tree.json, evidence/eed089bd8f88--anonymous--desktop/actions.json, evidence/eed089bd8f88--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--anonymous--desktop--1.4.4--f11851694799.json](assessments/eed089bd8f88--anonymous--desktop--1.4.4--f11851694799.json)

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--dialog-open--desktop--1.4.4
対象: http://127.0.0.1:4330/ / dialog-open / desktop
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--dialog-open--desktop/page.png, evidence/eed089bd8f88--dialog-open--desktop/inventory.json, evidence/eed089bd8f88--dialog-open--desktop/dom.html, evidence/eed089bd8f88--dialog-open--desktop/accessibility-tree.json, evidence/eed089bd8f88--dialog-open--desktop/actions.json, evidence/eed089bd8f88--dialog-open--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / dialog-open / desktop

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--dialog-open--desktop/page.png, evidence/eed089bd8f88--dialog-open--desktop/inventory.json, evidence/eed089bd8f88--dialog-open--desktop/dom.html, evidence/eed089bd8f88--dialog-open--desktop/accessibility-tree.json, evidence/eed089bd8f88--dialog-open--desktop/actions.json, evidence/eed089bd8f88--dialog-open--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--dialog-open--desktop--1.4.4--3935455af980.json](assessments/eed089bd8f88--dialog-open--desktop--1.4.4--3935455af980.json)

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--dialog-closed--desktop--1.4.4
対象: http://127.0.0.1:4330/ / dialog-closed / desktop
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--dialog-closed--desktop/page.png, evidence/eed089bd8f88--dialog-closed--desktop/inventory.json, evidence/eed089bd8f88--dialog-closed--desktop/dom.html, evidence/eed089bd8f88--dialog-closed--desktop/accessibility-tree.json, evidence/eed089bd8f88--dialog-closed--desktop/actions.json, evidence/eed089bd8f88--dialog-closed--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / dialog-closed / desktop

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--dialog-closed--desktop/page.png, evidence/eed089bd8f88--dialog-closed--desktop/inventory.json, evidence/eed089bd8f88--dialog-closed--desktop/dom.html, evidence/eed089bd8f88--dialog-closed--desktop/accessibility-tree.json, evidence/eed089bd8f88--dialog-closed--desktop/actions.json, evidence/eed089bd8f88--dialog-closed--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/000-home-initial.png, evidence/methods/browser/desktop/000-home-initial.json, evidence/methods/browser/desktop/000-home-initial-ax.json, evidence/methods/browser/desktop/005-dialog-open.png, evidence/methods/browser/desktop/005-dialog-open.json, evidence/methods/browser/desktop/005-dialog-open-ax.json, evidence/methods/browser/desktop/004-hybrid-count-six.png, evidence/methods/browser/desktop/004-hybrid-count-six.json, evidence/methods/browser/desktop/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--dialog-closed--desktop--1.4.4--9e15863a2347.json](assessments/eed089bd8f88--dialog-closed--desktop--1.4.4--9e15863a2347.json)

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--initial--narrow--1.4.4
対象: http://127.0.0.1:4330/ / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--initial--narrow/page.png, evidence/eed089bd8f88--initial--narrow/inventory.json, evidence/eed089bd8f88--initial--narrow/dom.html, evidence/eed089bd8f88--initial--narrow/accessibility-tree.json, evidence/eed089bd8f88--initial--narrow/actions.json, evidence/eed089bd8f88--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / initial / narrow

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--initial--narrow/page.png, evidence/eed089bd8f88--initial--narrow/inventory.json, evidence/eed089bd8f88--initial--narrow/dom.html, evidence/eed089bd8f88--initial--narrow/accessibility-tree.json, evidence/eed089bd8f88--initial--narrow/actions.json, evidence/eed089bd8f88--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--initial--narrow--1.4.4--f9bf19c26017.json](assessments/eed089bd8f88--initial--narrow--1.4.4--f9bf19c26017.json)

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--anonymous--narrow--1.4.4
対象: http://127.0.0.1:4330/ / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--anonymous--narrow/page.png, evidence/eed089bd8f88--anonymous--narrow/inventory.json, evidence/eed089bd8f88--anonymous--narrow/dom.html, evidence/eed089bd8f88--anonymous--narrow/accessibility-tree.json, evidence/eed089bd8f88--anonymous--narrow/actions.json, evidence/eed089bd8f88--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / anonymous / narrow

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--anonymous--narrow/page.png, evidence/eed089bd8f88--anonymous--narrow/inventory.json, evidence/eed089bd8f88--anonymous--narrow/dom.html, evidence/eed089bd8f88--anonymous--narrow/accessibility-tree.json, evidence/eed089bd8f88--anonymous--narrow/actions.json, evidence/eed089bd8f88--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--anonymous--narrow--1.4.4--adfe374d21fd.json](assessments/eed089bd8f88--anonymous--narrow--1.4.4--adfe374d21fd.json)

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--dialog-open--narrow--1.4.4
対象: http://127.0.0.1:4330/ / dialog-open / narrow
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--dialog-open--narrow/page.png, evidence/eed089bd8f88--dialog-open--narrow/inventory.json, evidence/eed089bd8f88--dialog-open--narrow/dom.html, evidence/eed089bd8f88--dialog-open--narrow/accessibility-tree.json, evidence/eed089bd8f88--dialog-open--narrow/actions.json, evidence/eed089bd8f88--dialog-open--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / dialog-open / narrow

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--dialog-open--narrow/page.png, evidence/eed089bd8f88--dialog-open--narrow/inventory.json, evidence/eed089bd8f88--dialog-open--narrow/dom.html, evidence/eed089bd8f88--dialog-open--narrow/accessibility-tree.json, evidence/eed089bd8f88--dialog-open--narrow/actions.json, evidence/eed089bd8f88--dialog-open--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--dialog-open--narrow--1.4.4--ee2c355a012c.json](assessments/eed089bd8f88--dialog-open--narrow--1.4.4--ee2c355a012c.json)

## 1.4.4 テキストのサイズ変更

case_id: eed089bd8f88--dialog-closed--narrow--1.4.4
対象: http://127.0.0.1:4330/ / dialog-closed / narrow
現在の判定: cant_tell

引き継ぐ理由: 実ブラウザー拡大とHTML機能は確認済みだが、viewBoxで縮むSVG文字の実効拡大と別経路の条件を確定していない。
担当に必要な知識: SVGの文字拡大・画像内文字等の例外を確認できる担当
必要な環境: ホームのSVGと対象ブラウザーの利用者向け文字拡大の仕組み

調べた方法と結果:

- zoom, visual, flow, measurement: HTMLの本文・全操作は実ブラウザー200%でも保持して完了できた。一方、viewBoxとmax-widthで縮むSVG内文字の実効的な拡大と、画像内文字等の例外又は別の文字拡大経路の条件は確定していない。
  証拠: evidence/eed089bd8f88--dialog-closed--narrow/page.png, evidence/eed089bd8f88--dialog-closed--narrow/inventory.json, evidence/eed089bd8f88--dialog-closed--narrow/dom.html, evidence/eed089bd8f88--dialog-closed--narrow/accessibility-tree.json, evidence/eed089bd8f88--dialog-closed--narrow/actions.json, evidence/eed089bd8f88--dialog-closed--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

対象: SVG[role=img] のEdit/Review/Save / http://127.0.0.1:4330/ / dialog-closed / narrow

実行する操作:

1. SVGのEdit/Review/Saveのラベルについて、本文の対象と例外を照合する
2. 対象なら利用者が200%まで文字を拡大する実在の経路を操作し、実効サイズ、情報と機能の保持を確認する

判定条件: 少なくとも一つの利用可能な文字拡大方法で、200%までの途中を含め内容・機能を失わず実際の文字が拡大できるか。ブラウザーの倍率だけで実際の文字サイズや条件の充足を決めない
証拠: evidence/eed089bd8f88--dialog-closed--narrow/page.png, evidence/eed089bd8f88--dialog-closed--narrow/inventory.json, evidence/eed089bd8f88--dialog-closed--narrow/dom.html, evidence/eed089bd8f88--dialog-closed--narrow/accessibility-tree.json, evidence/eed089bd8f88--dialog-closed--narrow/actions.json, evidence/eed089bd8f88--dialog-closed--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/000-home-initial.png, evidence/methods/browser/narrow/000-home-initial.json, evidence/methods/browser/narrow/000-home-initial-ax.json, evidence/methods/browser/narrow/005-dialog-open.png, evidence/methods/browser/narrow/005-dialog-open.json, evidence/methods/browser/narrow/005-dialog-open-ax.json, evidence/methods/browser/narrow/004-hybrid-count-six.png, evidence/methods/browser/narrow/004-hybrid-count-six.json, evidence/methods/browser/narrow/004-hybrid-count-six-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/eed089bd8f88--dialog-closed--narrow--1.4.4--702a72743f17.json](assessments/eed089bd8f88--dialog-closed--narrow--1.4.4--702a72743f17.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--initial--desktop--1.2.2
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--1.2.2--0e39c958abf3.json](assessments/ee1978846e1c--initial--desktop--1.2.2--0e39c958abf3.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--initial--desktop--1.2.3
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--1.2.3--043222ca1d8c.json](assessments/ee1978846e1c--initial--desktop--1.2.3--043222ca1d8c.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--initial--desktop--1.2.5
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--1.2.5--185efff362b4.json](assessments/ee1978846e1c--initial--desktop--1.2.5--185efff362b4.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--initial--desktop--1.3.3
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--1.3.3--736ad6332461.json](assessments/ee1978846e1c--initial--desktop--1.3.3--736ad6332461.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--initial--desktop--1.4.3
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--1.4.3--8fa3523d061e.json](assessments/ee1978846e1c--initial--desktop--1.4.3--8fa3523d061e.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--initial--desktop--1.4.5
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--1.4.5--2c2bbe95da3f.json](assessments/ee1978846e1c--initial--desktop--1.4.5--2c2bbe95da3f.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--initial--desktop--1.4.12
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--1.4.12--fc8412a36e80.json](assessments/ee1978846e1c--initial--desktop--1.4.12--fc8412a36e80.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--initial--desktop--2.3.1
対象: http://127.0.0.1:4330/media / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / desktop

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--initial--desktop/page.png, evidence/ee1978846e1c--initial--desktop/inventory.json, evidence/ee1978846e1c--initial--desktop/dom.html, evidence/ee1978846e1c--initial--desktop/accessibility-tree.json, evidence/ee1978846e1c--initial--desktop/actions.json, evidence/ee1978846e1c--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--desktop--2.3.1--ba4542421fee.json](assessments/ee1978846e1c--initial--desktop--2.3.1--ba4542421fee.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--anonymous--desktop--1.2.2
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--1.2.2--59c016e4faaf.json](assessments/ee1978846e1c--anonymous--desktop--1.2.2--59c016e4faaf.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--anonymous--desktop--1.2.3
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--1.2.3--3d8f94ca19a3.json](assessments/ee1978846e1c--anonymous--desktop--1.2.3--3d8f94ca19a3.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--anonymous--desktop--1.2.5
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--1.2.5--657ee03c9827.json](assessments/ee1978846e1c--anonymous--desktop--1.2.5--657ee03c9827.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--anonymous--desktop--1.3.3
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--1.3.3--3913b5694978.json](assessments/ee1978846e1c--anonymous--desktop--1.3.3--3913b5694978.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--anonymous--desktop--1.4.3
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--1.4.3--1bcacbc9f585.json](assessments/ee1978846e1c--anonymous--desktop--1.4.3--1bcacbc9f585.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--anonymous--desktop--1.4.5
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--1.4.5--905f8ede6745.json](assessments/ee1978846e1c--anonymous--desktop--1.4.5--905f8ede6745.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--anonymous--desktop--1.4.12
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--1.4.12--3fb0eddb14ac.json](assessments/ee1978846e1c--anonymous--desktop--1.4.12--3fb0eddb14ac.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--anonymous--desktop--2.3.1
対象: http://127.0.0.1:4330/media / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / desktop

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--anonymous--desktop/page.png, evidence/ee1978846e1c--anonymous--desktop/inventory.json, evidence/ee1978846e1c--anonymous--desktop/dom.html, evidence/ee1978846e1c--anonymous--desktop/accessibility-tree.json, evidence/ee1978846e1c--anonymous--desktop/actions.json, evidence/ee1978846e1c--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--desktop--2.3.1--e43e9d3b7a37.json](assessments/ee1978846e1c--anonymous--desktop--2.3.1--e43e9d3b7a37.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--captions-on--desktop--1.2.2
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--1.2.2--194e267d7887.json](assessments/ee1978846e1c--captions-on--desktop--1.2.2--194e267d7887.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--captions-on--desktop--1.2.3
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--1.2.3--82828bb61e20.json](assessments/ee1978846e1c--captions-on--desktop--1.2.3--82828bb61e20.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--captions-on--desktop--1.2.5
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--1.2.5--be6bb5c0cfc4.json](assessments/ee1978846e1c--captions-on--desktop--1.2.5--be6bb5c0cfc4.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--captions-on--desktop--1.3.3
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--1.3.3--db5a62129ac0.json](assessments/ee1978846e1c--captions-on--desktop--1.3.3--db5a62129ac0.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--captions-on--desktop--1.4.3
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--1.4.3--6f1a01bb36e1.json](assessments/ee1978846e1c--captions-on--desktop--1.4.3--6f1a01bb36e1.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--captions-on--desktop--1.4.5
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--1.4.5--6950060b7961.json](assessments/ee1978846e1c--captions-on--desktop--1.4.5--6950060b7961.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--captions-on--desktop--1.4.12
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--1.4.12--d4819c996f6a.json](assessments/ee1978846e1c--captions-on--desktop--1.4.12--d4819c996f6a.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--captions-on--desktop--2.3.1
対象: http://127.0.0.1:4330/media / captions-on / desktop
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / desktop

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--captions-on--desktop/page.png, evidence/ee1978846e1c--captions-on--desktop/inventory.json, evidence/ee1978846e1c--captions-on--desktop/dom.html, evidence/ee1978846e1c--captions-on--desktop/accessibility-tree.json, evidence/ee1978846e1c--captions-on--desktop/actions.json, evidence/ee1978846e1c--captions-on--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--desktop--2.3.1--0691e5b25615.json](assessments/ee1978846e1c--captions-on--desktop--2.3.1--0691e5b25615.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--video-ended--desktop--1.2.2
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--1.2.2--be53bbfe78dd.json](assessments/ee1978846e1c--video-ended--desktop--1.2.2--be53bbfe78dd.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--video-ended--desktop--1.2.3
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--1.2.3--752be936e6f6.json](assessments/ee1978846e1c--video-ended--desktop--1.2.3--752be936e6f6.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--video-ended--desktop--1.2.5
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--1.2.5--ad64d794bcd9.json](assessments/ee1978846e1c--video-ended--desktop--1.2.5--ad64d794bcd9.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--video-ended--desktop--1.3.3
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--1.3.3--448e2de9f56c.json](assessments/ee1978846e1c--video-ended--desktop--1.3.3--448e2de9f56c.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--video-ended--desktop--1.4.3
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--1.4.3--c81541ff0246.json](assessments/ee1978846e1c--video-ended--desktop--1.4.3--c81541ff0246.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--video-ended--desktop--1.4.5
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--1.4.5--888d391a8cd9.json](assessments/ee1978846e1c--video-ended--desktop--1.4.5--888d391a8cd9.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--video-ended--desktop--1.4.12
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--1.4.12--60545df04c33.json](assessments/ee1978846e1c--video-ended--desktop--1.4.12--60545df04c33.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--video-ended--desktop--2.3.1
対象: http://127.0.0.1:4330/media / video-ended / desktop
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / desktop

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--video-ended--desktop/page.png, evidence/ee1978846e1c--video-ended--desktop/inventory.json, evidence/ee1978846e1c--video-ended--desktop/dom.html, evidence/ee1978846e1c--video-ended--desktop/accessibility-tree.json, evidence/ee1978846e1c--video-ended--desktop/actions.json, evidence/ee1978846e1c--video-ended--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/browser/desktop/015-captions-playing.png, evidence/methods/browser/desktop/015-captions-playing.json, evidence/methods/browser/desktop/015-captions-playing-ax.json, evidence/methods/browser/desktop/016-video-paused.png, evidence/methods/browser/desktop/016-video-paused.json, evidence/methods/browser/desktop/016-video-paused-ax.json, evidence/methods/browser/desktop/017-video-ended.png, evidence/methods/browser/desktop/017-video-ended.json, evidence/methods/browser/desktop/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--desktop--2.3.1--0d57ef21dd4c.json](assessments/ee1978846e1c--video-ended--desktop--2.3.1--0d57ef21dd4c.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--initial--narrow--1.2.2
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--1.2.2--96f743fd9f67.json](assessments/ee1978846e1c--initial--narrow--1.2.2--96f743fd9f67.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--initial--narrow--1.2.3
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--1.2.3--1db083f5cbe1.json](assessments/ee1978846e1c--initial--narrow--1.2.3--1db083f5cbe1.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--initial--narrow--1.2.5
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--1.2.5--0bf8d60692c4.json](assessments/ee1978846e1c--initial--narrow--1.2.5--0bf8d60692c4.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--initial--narrow--1.3.3
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--1.3.3--4e788dac40f2.json](assessments/ee1978846e1c--initial--narrow--1.3.3--4e788dac40f2.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--initial--narrow--1.4.3
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--1.4.3--a1f6d3d3e624.json](assessments/ee1978846e1c--initial--narrow--1.4.3--a1f6d3d3e624.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--initial--narrow--1.4.5
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--1.4.5--cd598f5f8db7.json](assessments/ee1978846e1c--initial--narrow--1.4.5--cd598f5f8db7.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--initial--narrow--1.4.12
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--1.4.12--0b1ac65d1dec.json](assessments/ee1978846e1c--initial--narrow--1.4.12--0b1ac65d1dec.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--initial--narrow--2.3.1
対象: http://127.0.0.1:4330/media / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / initial / narrow

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--initial--narrow/page.png, evidence/ee1978846e1c--initial--narrow/inventory.json, evidence/ee1978846e1c--initial--narrow/dom.html, evidence/ee1978846e1c--initial--narrow/accessibility-tree.json, evidence/ee1978846e1c--initial--narrow/actions.json, evidence/ee1978846e1c--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--initial--narrow--2.3.1--9c0a214138d4.json](assessments/ee1978846e1c--initial--narrow--2.3.1--9c0a214138d4.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--anonymous--narrow--1.2.2
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--1.2.2--beedaa06448c.json](assessments/ee1978846e1c--anonymous--narrow--1.2.2--beedaa06448c.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--anonymous--narrow--1.2.3
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--1.2.3--566b421e10fa.json](assessments/ee1978846e1c--anonymous--narrow--1.2.3--566b421e10fa.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--anonymous--narrow--1.2.5
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--1.2.5--20f61dda3165.json](assessments/ee1978846e1c--anonymous--narrow--1.2.5--20f61dda3165.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--anonymous--narrow--1.3.3
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--1.3.3--a1aef2262206.json](assessments/ee1978846e1c--anonymous--narrow--1.3.3--a1aef2262206.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--anonymous--narrow--1.4.3
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--1.4.3--c02aa0272655.json](assessments/ee1978846e1c--anonymous--narrow--1.4.3--c02aa0272655.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--anonymous--narrow--1.4.5
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--1.4.5--ecc09f36f102.json](assessments/ee1978846e1c--anonymous--narrow--1.4.5--ecc09f36f102.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--anonymous--narrow--1.4.12
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--1.4.12--162253cd96ac.json](assessments/ee1978846e1c--anonymous--narrow--1.4.12--162253cd96ac.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--anonymous--narrow--2.3.1
対象: http://127.0.0.1:4330/media / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / anonymous / narrow

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--anonymous--narrow/page.png, evidence/ee1978846e1c--anonymous--narrow/inventory.json, evidence/ee1978846e1c--anonymous--narrow/dom.html, evidence/ee1978846e1c--anonymous--narrow/accessibility-tree.json, evidence/ee1978846e1c--anonymous--narrow/actions.json, evidence/ee1978846e1c--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--anonymous--narrow--2.3.1--1d8c0b115db6.json](assessments/ee1978846e1c--anonymous--narrow--2.3.1--1d8c0b115db6.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--captions-on--narrow--1.2.2
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--1.2.2--423133fa19e9.json](assessments/ee1978846e1c--captions-on--narrow--1.2.2--423133fa19e9.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--captions-on--narrow--1.2.3
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--1.2.3--be9853416f9d.json](assessments/ee1978846e1c--captions-on--narrow--1.2.3--be9853416f9d.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--captions-on--narrow--1.2.5
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--1.2.5--1d6489d5d4c6.json](assessments/ee1978846e1c--captions-on--narrow--1.2.5--1d6489d5d4c6.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--captions-on--narrow--1.3.3
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--1.3.3--30ff992fb1fc.json](assessments/ee1978846e1c--captions-on--narrow--1.3.3--30ff992fb1fc.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--captions-on--narrow--1.4.3
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--1.4.3--12e30613012e.json](assessments/ee1978846e1c--captions-on--narrow--1.4.3--12e30613012e.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--captions-on--narrow--1.4.5
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--1.4.5--6a20b2b45cb4.json](assessments/ee1978846e1c--captions-on--narrow--1.4.5--6a20b2b45cb4.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--captions-on--narrow--1.4.12
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--1.4.12--eb473fa98faf.json](assessments/ee1978846e1c--captions-on--narrow--1.4.12--eb473fa98faf.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--captions-on--narrow--2.3.1
対象: http://127.0.0.1:4330/media / captions-on / narrow
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / captions-on / narrow

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--captions-on--narrow/page.png, evidence/ee1978846e1c--captions-on--narrow/inventory.json, evidence/ee1978846e1c--captions-on--narrow/dom.html, evidence/ee1978846e1c--captions-on--narrow/accessibility-tree.json, evidence/ee1978846e1c--captions-on--narrow/actions.json, evidence/ee1978846e1c--captions-on--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--captions-on--narrow--2.3.1--bb6d2cc9b4b6.json](assessments/ee1978846e1c--captions-on--narrow--2.3.1--bb6d2cc9b4b6.json)

## 1.2.2 キャプション (収録済)

case_id: ee1978846e1c--video-ended--narrow--1.2.2
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: 字幕を元の音声と全区間比較する聴取能力がこのAIにない。
担当に必要な知識: 英語の発話・必要な音・字幕を比較できる担当
必要な環境: 元の音声を聴取し、字幕を同時に表示できる実プレーヤー

調べた方法と結果:

- media, semantic: 7秒の英語音声を含む収録済み動画と英語VTTがある。字幕の有効化、cue、実表示、再生・一時停止・終了は確認したが、発話・必要な音・話者と字幕の全内容の比較は未確認。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. 英語字幕を有効にしてvideo#clipを0〜7秒まで再生する
2. 全発話、必要な音、話者、情報の抜けと同期を元音声・映像と比較し、区間ごとに記録する

判定条件: 必要な音声情報が同期したキャプションで得られるか。本文の例外を確認する
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--1.2.2--112f4f230861.json](assessments/ee1978846e1c--video-ended--narrow--1.2.2--112f4f230861.json)

## 1.2.3 音声解説、又はメディアに対する代替 (収録済)

case_id: ee1978846e1c--video-ended--narrow--1.2.3
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: 文章代替と元音声・映像の全情報の対応を確定する聴取ができない。
担当に必要な知識: 英語の元媒体と文章による代替を比較できる担当
必要な環境: 元音声、映像、#transcriptの文章を同時に確認できる環境

調べた方法と結果:

- media, semantic: 映像と英語の文章による説明がある。元の音声・映像と文章代替の全情報、順序、必要な描写の対応は全区間で比較できていない。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. video#clipの0〜7秒の全情報と表示順序を確認する
2. #transcriptが必要な音声・視覚情報と順序を含むか、採用する代替の条件と比較する

判定条件: 音声解説又はメディア代替で必要な情報を得られるか。文章の代替では情報の順序と操作結果も確認する。音声解説の経路と文章の経路を一律に両方必須にしない
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--1.2.3--508099d820e8.json](assessments/ee1978846e1c--video-ended--narrow--1.2.3--508099d820e8.json)

## 1.2.5 音声解説 (収録済)

case_id: ee1978846e1c--video-ended--narrow--1.2.5
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: 収録済み映像に必要な音声解説が元音声で得られるか全区間の聴取ができない。
担当に必要な知識: 英語音声と映像の重要情報・音声解説を比較できる担当
必要な環境: 元の映像と音声を全区間再生し、解説の有無と内容を確認できる環境

調べた方法と結果:

- media, semantic: 収録済み映像の必要な視覚情報を、元の音声と全区間比較する聴取が未実施。文章代替の存在だけでAAの音声解説の条件を満たすとはしていない。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. video#clipの0〜7秒で意味のある視覚情報を全て特定する
2. その情報が音声から取得できるか、必要な音声解説の提供と内容を比較する

判定条件: 元音声に含まれない必要な映像情報が音声解説で伝わるか。文章代替だけでこのAA基準を通過させない
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--1.2.5--2b7adb6fd32c.json](assessments/ee1978846e1c--video-ended--narrow--1.2.5--2b7adb6fd32c.json)

## 1.3.3 感覚的な特徴

case_id: ee1978846e1c--video-ended--narrow--1.3.3
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの指示は調べたが、動画の発話の指示を全区間で比較できない。
担当に必要な知識: 英語の操作指示と映像を比較できる担当
必要な環境: 動画の元音声と映像

調べた方法と結果:

- visual, semantic: HTMLの操作は表示名で識別できる。動画の発話に含まれる指示が色・位置等だけに依存していないかは、元音声と映像の比較が残る。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. video#clipの全発話のうち理解・操作の指示を特定する
2. 色・位置・形・音だけに依存していないか、使える名前と文脈を比較する

判定条件: 感覚的な特徴だけに依存する指示がないか
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--1.3.3--e0b13532a425.json](assessments/ee1978846e1c--video-ended--narrow--1.3.3--e0b13532a425.json)

## 1.4.3 コントラスト (最低限)

case_id: ee1978846e1c--video-ended--narrow--1.4.3
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLと字幕の指定色は調べたが、圧縮映像の少数画素から全編の文字色を確定する方法は未校正。
担当に必要な知識: 圧縮映像と字幕の文字のコントラストを測定できる担当
必要な環境: 元の映像、字幕と実プレーヤー、前景・背景を識別できる測定手段

調べた方法と結果:

- dom, visual, measurement: HTMLの文字は実際の指定色・画面から比を確認した。動画内文字は圧縮画像で、取り出した一部画素の比だけでは全表示区間の文字色を確定していない。全編の文字・字幕との比の確認を残す。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. video#clipの全発生区間の文字と字幕を列挙し、文字サイズ・太さ・例外を確認する
2. アンチエイリアスの縁を前景色にせず実際の前景・背景を測り、本文の4.5:1又は大きい文字の3:1等と比較する

判定条件: 通常4.5:1、大きな文字3:1等を原典の定義と例外に沿って判定する。ptとCSS pxを区別し丸めない
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/measurements/contrasts.json, evidence/methods/media-analysis/frame-colors.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--1.4.3--0485783e7410.json](assessments/ee1978846e1c--video-ended--narrow--1.4.3--0485783e7410.json)

## 1.4.5 文字画像

case_id: ee1978846e1c--video-ended--narrow--1.4.5
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: 録画された模擬UI内の文字について、画像内文字の適用範囲・提示の例外の判断を残す。
担当に必要な知識: 媒体内の文字とWCAGの画像内文字・例外を判断できる担当
必要な環境: video#clip、文章代替、採用したWCAG本文と定義

調べた方法と結果:

- visual, dom, semantic: HTMLには実文字を使う。収録動画の模擬UI内の文字について、本文の画像内文字の適用範囲・必要な提示の例外・同じ情報を伝える方法の判断を残す。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. 模擬UIの文字が本文の画像内文字の対象になるか、図・動画の文脈と定義を照合する
2. 適用する場合、実文字による同じ情報の提示、カスタマイズ又は必要な提示の例外の根拠を確認する

判定条件: 原典の例外を除き文字画像への依存がないか
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json, evidence/methods/media-analysis/frame-6.png, evidence/methods/media-analysis/frame-colors.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--1.4.5--3f64fd63232d.json](assessments/ee1978846e1c--video-ended--narrow--1.4.5--3f64fd63232d.json)

## 1.4.12 テキストの間隔

case_id: ee1978846e1c--video-ended--narrow--1.4.12
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: HTMLの上書きと機能は確認済み。ネイティブWebVTT字幕で全設定を確認する方法は未校正。
担当に必要な知識: WebVTTと対象ブラウザーの字幕表示・文字間隔を確認できる担当
必要な環境: 対象Chromium、元のVTT、字幕を表示して各サポート設定を検証する手段

調べた方法と結果:

- dom, visual, flow: HTMLへ4設定を同時に適用し、全操作と全文を確認した。ネイティブWebVTT字幕では、各設定が適用できる範囲と字幕全体の保持の確認が残る。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. 実プレーヤーで英語字幕を表示し、WebVTTでサポートされる本文の各設定を特定する
2. 変更可能な行高・段落・字間・単語間の条件を適用し、全字幕と操作の欠落・重なりを比較する

判定条件: 本文の文字体系の条件に沿い、内容・機能の損失がないか
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/zoom-200/observations.json, evidence/methods/browser/zoom-400/observations.json, evidence/methods/browser/desktop-spacing/observations.json, evidence/methods/browser/narrow-spacing/observations.json, evidence/methods/extra/spacing-scroll.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--1.4.12--857625defd4b.json](assessments/ee1978846e1c--video-ended--narrow--1.4.12--857625defd4b.json)

## 2.3.1 3 回の閃光、又は閾値以下

case_id: ee1978846e1c--video-ended--narrow--2.3.1
対象: http://127.0.0.1:4330/media / video-ended / narrow
現在の判定: cant_tell

引き継ぐ理由: 全フレームを取得できるが、本文の一般・赤色閃光と面積を検証済みの分析器で評価できていない。
担当に必要な知識: WCAGの一般閃光・赤色閃光・面積・時間を分析できる担当
必要な環境: 元の映像全フレームと対象の表示条件、両閃光閾値を評価できる検証済みの分析器

調べた方法と結果:

- flash-analysis, media, measurement: 7秒の動画の全復号とフレームの取得はできるが、一般閃光・赤色閃光・面積の本文の閾値を検証済みの分析方法で全編評価する確認が残る。画面差分や目視だけで安全としていない。
  証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

対象: video#clip と全字幕・代替・該当する条件 / http://127.0.0.1:4330/media / video-ended / narrow

実行する操作:

1. video#clipの0〜7秒を全フレーム・連続する任意の1秒で分析する
2. 毎秒3回以下又は一般・赤色閃光の両閾値以下か、表示面積の条件と併せて記録する

判定条件: 閃光回数又は閾値の要件を満たすか。肉眼だけで安全と判定せず、分析不能は未確認にする
証拠: evidence/ee1978846e1c--video-ended--narrow/page.png, evidence/ee1978846e1c--video-ended--narrow/inventory.json, evidence/ee1978846e1c--video-ended--narrow/dom.html, evidence/ee1978846e1c--video-ended--narrow/accessibility-tree.json, evidence/ee1978846e1c--video-ended--narrow/actions.json, evidence/ee1978846e1c--video-ended--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/browser/narrow/015-captions-playing.png, evidence/methods/browser/narrow/015-captions-playing.json, evidence/methods/browser/narrow/015-captions-playing-ax.json, evidence/methods/browser/narrow/016-video-paused.png, evidence/methods/browser/narrow/016-video-paused.json, evidence/methods/browser/narrow/016-video-paused-ax.json, evidence/methods/browser/narrow/017-video-ended.png, evidence/methods/browser/narrow/017-video-ended.json, evidence/methods/browser/narrow/017-video-ended-ax.json, evidence/methods/browser/source/clip.webm, evidence/methods/browser/source/captions.vtt, evidence/methods/media-analysis/source-provenance.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/ee1978846e1c--video-ended--narrow--2.3.1--93da37dfeff9.json](assessments/ee1978846e1c--video-ended--narrow--2.3.1--93da37dfeff9.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--initial--desktop--4.1.3
対象: http://127.0.0.1:4330/login / initial / desktop
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--initial--desktop/page.png, evidence/2a14ee6fac28--initial--desktop/inventory.json, evidence/2a14ee6fac28--initial--desktop/dom.html, evidence/2a14ee6fac28--initial--desktop/accessibility-tree.json, evidence/2a14ee6fac28--initial--desktop/actions.json, evidence/2a14ee6fac28--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / initial / desktop

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--initial--desktop/page.png, evidence/2a14ee6fac28--initial--desktop/inventory.json, evidence/2a14ee6fac28--initial--desktop/dom.html, evidence/2a14ee6fac28--initial--desktop/accessibility-tree.json, evidence/2a14ee6fac28--initial--desktop/actions.json, evidence/2a14ee6fac28--initial--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--initial--desktop--4.1.3--06644c0375f8.json](assessments/2a14ee6fac28--initial--desktop--4.1.3--06644c0375f8.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--anonymous--desktop--4.1.3
対象: http://127.0.0.1:4330/login / anonymous / desktop
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--anonymous--desktop/page.png, evidence/2a14ee6fac28--anonymous--desktop/inventory.json, evidence/2a14ee6fac28--anonymous--desktop/dom.html, evidence/2a14ee6fac28--anonymous--desktop/accessibility-tree.json, evidence/2a14ee6fac28--anonymous--desktop/actions.json, evidence/2a14ee6fac28--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / anonymous / desktop

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--anonymous--desktop/page.png, evidence/2a14ee6fac28--anonymous--desktop/inventory.json, evidence/2a14ee6fac28--anonymous--desktop/dom.html, evidence/2a14ee6fac28--anonymous--desktop/accessibility-tree.json, evidence/2a14ee6fac28--anonymous--desktop/actions.json, evidence/2a14ee6fac28--anonymous--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--anonymous--desktop--4.1.3--7d7875f59fcd.json](assessments/2a14ee6fac28--anonymous--desktop--4.1.3--7d7875f59fcd.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--login-error--desktop--4.1.3
対象: http://127.0.0.1:4330/login / login-error / desktop
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--login-error--desktop/page.png, evidence/2a14ee6fac28--login-error--desktop/inventory.json, evidence/2a14ee6fac28--login-error--desktop/dom.html, evidence/2a14ee6fac28--login-error--desktop/accessibility-tree.json, evidence/2a14ee6fac28--login-error--desktop/actions.json, evidence/2a14ee6fac28--login-error--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / login-error / desktop

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--login-error--desktop/page.png, evidence/2a14ee6fac28--login-error--desktop/inventory.json, evidence/2a14ee6fac28--login-error--desktop/dom.html, evidence/2a14ee6fac28--login-error--desktop/accessibility-tree.json, evidence/2a14ee6fac28--login-error--desktop/actions.json, evidence/2a14ee6fac28--login-error--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--login-error--desktop--4.1.3--7e99e15002b5.json](assessments/2a14ee6fac28--login-error--desktop--4.1.3--7e99e15002b5.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--login-success--desktop--4.1.3
対象: http://127.0.0.1:4330/login / login-success / desktop
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--login-success--desktop/page.png, evidence/2a14ee6fac28--login-success--desktop/inventory.json, evidence/2a14ee6fac28--login-success--desktop/dom.html, evidence/2a14ee6fac28--login-success--desktop/accessibility-tree.json, evidence/2a14ee6fac28--login-success--desktop/actions.json, evidence/2a14ee6fac28--login-success--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / login-success / desktop

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--login-success--desktop/page.png, evidence/2a14ee6fac28--login-success--desktop/inventory.json, evidence/2a14ee6fac28--login-success--desktop/dom.html, evidence/2a14ee6fac28--login-success--desktop/accessibility-tree.json, evidence/2a14ee6fac28--login-success--desktop/actions.json, evidence/2a14ee6fac28--login-success--desktop/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/desktop/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/desktop/019-login-error.png, evidence/methods/browser/desktop/019-login-error.json, evidence/methods/browser/desktop/019-login-error-ax.json, evidence/methods/browser/desktop/020-login-pasted.png, evidence/methods/browser/desktop/020-login-pasted.json, evidence/methods/browser/desktop/020-login-pasted-ax.json, evidence/methods/browser/desktop/021-login-success.png, evidence/methods/browser/desktop/021-login-success.json, evidence/methods/browser/desktop/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--login-success--desktop--4.1.3--c07718d38198.json](assessments/2a14ee6fac28--login-success--desktop--4.1.3--c07718d38198.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--initial--narrow--4.1.3
対象: http://127.0.0.1:4330/login / initial / narrow
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--initial--narrow/page.png, evidence/2a14ee6fac28--initial--narrow/inventory.json, evidence/2a14ee6fac28--initial--narrow/dom.html, evidence/2a14ee6fac28--initial--narrow/accessibility-tree.json, evidence/2a14ee6fac28--initial--narrow/actions.json, evidence/2a14ee6fac28--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / initial / narrow

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--initial--narrow/page.png, evidence/2a14ee6fac28--initial--narrow/inventory.json, evidence/2a14ee6fac28--initial--narrow/dom.html, evidence/2a14ee6fac28--initial--narrow/accessibility-tree.json, evidence/2a14ee6fac28--initial--narrow/actions.json, evidence/2a14ee6fac28--initial--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--initial--narrow--4.1.3--a00b187dfdf1.json](assessments/2a14ee6fac28--initial--narrow--4.1.3--a00b187dfdf1.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--anonymous--narrow--4.1.3
対象: http://127.0.0.1:4330/login / anonymous / narrow
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--anonymous--narrow/page.png, evidence/2a14ee6fac28--anonymous--narrow/inventory.json, evidence/2a14ee6fac28--anonymous--narrow/dom.html, evidence/2a14ee6fac28--anonymous--narrow/accessibility-tree.json, evidence/2a14ee6fac28--anonymous--narrow/actions.json, evidence/2a14ee6fac28--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / anonymous / narrow

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--anonymous--narrow/page.png, evidence/2a14ee6fac28--anonymous--narrow/inventory.json, evidence/2a14ee6fac28--anonymous--narrow/dom.html, evidence/2a14ee6fac28--anonymous--narrow/accessibility-tree.json, evidence/2a14ee6fac28--anonymous--narrow/actions.json, evidence/2a14ee6fac28--anonymous--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--anonymous--narrow--4.1.3--7eabdda339f4.json](assessments/2a14ee6fac28--anonymous--narrow--4.1.3--7eabdda339f4.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--login-error--narrow--4.1.3
対象: http://127.0.0.1:4330/login / login-error / narrow
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--login-error--narrow/page.png, evidence/2a14ee6fac28--login-error--narrow/inventory.json, evidence/2a14ee6fac28--login-error--narrow/dom.html, evidence/2a14ee6fac28--login-error--narrow/accessibility-tree.json, evidence/2a14ee6fac28--login-error--narrow/actions.json, evidence/2a14ee6fac28--login-error--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / login-error / narrow

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--login-error--narrow/page.png, evidence/2a14ee6fac28--login-error--narrow/inventory.json, evidence/2a14ee6fac28--login-error--narrow/dom.html, evidence/2a14ee6fac28--login-error--narrow/accessibility-tree.json, evidence/2a14ee6fac28--login-error--narrow/actions.json, evidence/2a14ee6fac28--login-error--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--login-error--narrow--4.1.3--ef5ba5611bd7.json](assessments/2a14ee6fac28--login-error--narrow--4.1.3--ef5ba5611bd7.json)

## 4.1.3 ステータスメッセージ

case_id: 2a14ee6fac28--login-success--narrow--4.1.3
対象: http://127.0.0.1:4330/login / login-success / narrow
現在の判定: cant_tell

引き継ぐ理由: 成功の文字とAXのlive属性はあるが、実Orcaで成功通知の発話を取得しなかった。alertと他ページのstatusは同じ実Orcaで取得した。
担当に必要な知識: WCAGのstatus messageと対象支援技術のサポートを判断できる担当
必要な環境: このビルド、Chromium156/Orca48.1のログ、利用環境に応じた別の支援技術

調べた方法と結果:

- flow, dom, screen-reader: 誤った資格情報のalertは実Orcaが読んだ。成功の文字は表示され、AXはrole=status/live=polite/atomic=trueであるが、同じ実キーで成功した後にOrcaの発話を取得しなかった。環境・支援技術の差又は適合性の判断を分けるため、人に引き継ぐ。
  証拠: evidence/2a14ee6fac28--login-success--narrow/page.png, evidence/2a14ee6fac28--login-success--narrow/inventory.json, evidence/2a14ee6fac28--login-success--narrow/dom.html, evidence/2a14ee6fac28--login-success--narrow/accessibility-tree.json, evidence/2a14ee6fac28--login-success--narrow/actions.json, evidence/2a14ee6fac28--login-success--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

対象: #login-status の成功通知 / http://127.0.0.1:4330/login / login-success / narrow

実行する操作:

1. Loginでデモ資格情報を入力してサインインし、焦点を動かさず成功通知が取得できるか確認する
2. role/statusの公開値、実際の支援技術の通知、環境固有の問題と適合性を比較して根拠を記録する

判定条件: 本文の対象となる通知を支援技術が提示できるか。全更新へのalert追加を一律要求しない
証拠: evidence/2a14ee6fac28--login-success--narrow/page.png, evidence/2a14ee6fac28--login-success--narrow/inventory.json, evidence/2a14ee6fac28--login-success--narrow/dom.html, evidence/2a14ee6fac28--login-success--narrow/accessibility-tree.json, evidence/2a14ee6fac28--login-success--narrow/actions.json, evidence/2a14ee6fac28--login-success--narrow/keyboard.json, evidence/methods/browser/executed-source.py.txt, evidence/methods/browser/source/app.js, evidence/methods/browser/source/app.css, evidence/methods/browser/server.py.txt, evidence/methods/discovery/discovery.json, evidence/methods/browser/narrow/observations.json, evidence/methods/native/home/screen-reader.json, evidence/methods/extra/login-native/screen-reader.json, evidence/methods/media-analysis/native/screen-reader.json, evidence/methods/browser/narrow/019-login-error.png, evidence/methods/browser/narrow/019-login-error.json, evidence/methods/browser/narrow/019-login-error-ax.json, evidence/methods/browser/narrow/020-login-pasted.png, evidence/methods/browser/narrow/020-login-pasted.json, evidence/methods/browser/narrow/020-login-pasted-ax.json, evidence/methods/browser/narrow/021-login-success.png, evidence/methods/browser/narrow/021-login-success.json, evidence/methods/browser/narrow/021-login-success-ax.json

結果の戻し方: 対象ごとの実測・比較した内容・判断根拠・証拠を受け取り、このcaseの新しい判定として記録する。元の判定は保持する。
元の判定: [assessments/2a14ee6fac28--login-success--narrow--4.1.3--64ed9d721a74.json](assessments/2a14ee6fac28--login-success--narrow--4.1.3--64ed9d721a74.json)

