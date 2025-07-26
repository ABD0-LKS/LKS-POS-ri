@@ .. @@
         # Create menu buttons
         buttons = [
             ("Dashboard(F1)", "📊", self.parent.show_dashboard),
-            ("Settings (F2)", "⚙️", None),
+            ("Settings (F2)", "⚙️", self.parent.show_settings),
             ("Direct sell (f3)", "🏪", self.parent.show_pos),
             ("Day State (F4)", "💰", None),
             ("Seller Account (F5)", "👤", None)