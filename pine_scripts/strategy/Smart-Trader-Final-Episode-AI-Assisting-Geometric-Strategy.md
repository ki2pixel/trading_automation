7 days ago

Introduction

The triangle is one of the oldest and most fundamental shapes in geometry. With three sides, three angles, and an inherently stable structure, triangles have been used throughout history to study ratio, direction, balance, and the relationships between points in space. From early measurement techniques to classical geometry, the triangle became a simple yet powerful language for describing how points relate to one another.\
This strategy brings that geometric idea into a trading framework. Instead of viewing price movement as a single line on a chart, price behavior is examined through triangular measurements: angle, distance, area, and centroid. The purpose of these measurements is to help observe how price expands, compresses, reacts, or shifts around key reference levels.\
In this model, the triangle is not decorative. It is used as a structured measurement method --- a way to translate market movement into geometric relationships that can be tested, tuned, and examined directly within TradingView.

ICS Coordinate Framework

On a trading chart, a triangle can be constructed across two different dimensions: time and price. Time moves horizontally from bar to bar, while price moves vertically according to the scale of the selected market. Since these two axes do not share the same unit, a raw visual angle on the chart can be inconsistent. The same movement may appear steeper or flatter depending on zoom level, chart scaling, symbol price, or timeframe.\
To solve this measurement problem, the strategy uses an ICS framework --- an Isotropic Coordinate System --- where both axes are treated on equal footing after normalization. In this framework, the vertical axis is transformed as log(price) / sigma, where sigma is a volatility estimate calculated using the Yang-Zhang method, and the horizontal axis is normalized as bars / lookback. This makes time displacement and price displacement dimensionally compatible before any geometric calculation is performed.\
Inside this normalized space, the triangle measurements are calculated mathematically rather than visually. Price displacement is measured as dy, time displacement as dx, the angle is calculated from atan(dy / dx), and the triangle area is calculated as 0.5 × |dy| × |dx|. The centroid is also derived from the triangle's transformed coordinates, allowing the model to track the geometric balance point of the measured movement.\
This is the main difference between ICS triangles and ordinary chart drawings. A regular triangle drawn on a chart depends heavily on visual scale and manual placement. In this strategy, the triangles are calculated structures. They translate price movement, time distance, and volatility-adjusted scale into one consistent geometric framework, making angle, distance, area, and centroid more comparable across different symbols, timeframes, and market conditions.

Frozen Anchors --- The Fixed Reference

Before any triangle can be measured, the model needs a fixed origin --- a point that does not move while the market continues to move around it. Without a stable reference, geometric measurements such as angle and distance would shift every bar, making it difficult to observe how a move develops over time.\
This strategy establishes its reference by scanning a lookback window and identifying three structural levels: the highest high becomes the ceiling, the lowest low becomes the floor, and the geometric mean of the two becomes the center. These three levels are then frozen at the bar where the scan completes. From that moment, the anchor holds still. Every new bar that follows extends the measurement further in time, and the geometric readings --- angle, distance, area, and centroid --- evolve continuously relative to a known, fixed origin.\
The anchor remains active as long as price stays within the frozen ceiling and floor. When the close breaks above the ceiling or below the floor, the structure is considered invalidated. The anchor deactivates, and a new one is established on the next qualified bar. This creates a natural cycle: structure forms, measurements develop within it, and when the structure breaks, the framework resets and begins again.\
A fixed origin matters because it provides stability --- the reference does not jitter with each new bar. It provides cumulative context --- the measurement reflects the full arc of movement since the anchor was set, not just the last step. And it provides structural meaning --- the anchor is built from real price extremes within the lookback window, not from an arbitrary level.\
The default lookback period is 23 bars. This is a prime number, positioned near the length of a typical trading month on many daily charts, but not directly aligned with many common cycle lengths such as 5, 10, 14, 20, or 21. The period is fully adjustable.\
Once the anchor is frozen, the strategy constructs several types of triangles from it --- each measuring a different geometric relationship between the fixed origin and the current bar. These triangle types and their individual roles are described in the next section.

[![snapshot](https://www.tradingview.com/x/xGhtUsvi/)](https://www.tradingview.com/x/xGhtUsvi/)

Frozen anchor levels on a daily chart. The strategy scans the lookback window to identify the Ceiling (highest high), Floor (lowest low), and Center (geometric mean). These three levels are locked at the freeze bar and held fixed while price continues to move. All triangle measurements originate from this shared reference. When the close breaks above the ceiling or below the floor, the anchor resets and a new cycle begin.

Five Triangle Types

Once the frozen anchors are in place, the strategy constructs five distinct triangles on every bar. Each triangle connects a frozen reference level to a specific point on the current candle, measuring a different geometric relationship within the ICS framework. Three of these --- Ceiling, Center, and Floor --- are main triangles that track how price moves relative to the upper, middle, and lower reference levels. The remaining two --- Pin Up and Pin Down --- are wick triangles that isolate the candle's shadow behavior relative to the ceiling and floor.\
All five triangles share the same ICS normalization: vertical displacement is measured as log(price) / sigma, and horizontal displacement as bars / lookback. This ensures that the geometric readings from each triangle --- angle, distance, area, and centroid --- are more comparable within the same normalized framework, regardless of which reference level or price point they originate from.\
The three main triangles are right triangles. Each one has three vertices: vertex A sits at the frozen reference level on the freeze bar; vertex B sits at the same frozen level on the current bar, forming the horizontal leg; and vertex C sits at the target price point on the current bar, forming the vertical leg. The hypotenuse runs from A to C. As each new bar arrives, vertex C moves --- both forward in time and up or down in price --- and the triangle's shape changes accordingly.

The two pin triangles have different constructions. Instead of measuring from the reference level to a single price point, each pin triangle uses three distinct vertices to isolate the candle's wick: vertex A sits at the frozen reference level on the freeze bar; vertex B sits at the candle's extreme (high or low) on the current bar; and vertex C sits at the nearest body edge (top or bottom of the real body) on the current bar. The vertical side BC is the wick itself. The two lines from A to B and from A to C form two sloped sides, and the angle between them --- measured at vertex A --- captures how much the wick fans out as seen from the frozen anchor.

[![snapshot](https://www.tradingview.com/x/GjVeYplj/)](https://www.tradingview.com/x/GjVeYplj/)

Five triangle types on a daily chart. Three main right triangles --- Ceiling (red), Center (cyan), and Floor (purple) --- connect the frozen anchor levels to the current bar's high, geometric mean, and low. Two pin triangles --- Pin Up (orange) and Pin Down (purple) --- isolate the upper and lower wicks relative to the ceiling and floor. All five triangles share ICS normalization and produce four independent metrics each: angle, distance, area, and centroid.

▲ Ceiling --- HH → High

The Ceiling triangle connects the frozen highest high to the current bar's high. Vertex A is the ceiling level at the freeze bar; vertex C is the current bar's high. This triangle tracks how the market's upper boundary behaves relative to the structural ceiling.\
When the current high is below the frozen ceiling, the angle is negative --- price is compressing beneath the reference. As the current high moves closer to the frozen ceiling in ICS space, the angle moves toward zero. A positive angle would mean price has exceeded the ceiling, but this is unlikely within an active anchor cycle because a close above the ceiling triggers a reset.\
The Ceiling triangle is useful for observing how strongly price pushes toward or retreats from the upper boundary of the frozen structure.

[![snapshot](https://www.tradingview.com/x/Pf4Htf5J/)](https://www.tradingview.com/x/Pf4Htf5J/)

◆ Center --- Mid → Mid

The Center triangle connects the frozen geometric mean to the current bar's geometric mean. The frozen center is calculated as √(HH × LL) at the freeze bar, and the current midpoint is √(High × Low) of the current bar. Both endpoints use the geometric mean rather than the arithmetic average, which gives proportional weight to the relationship between the two prices rather than their sum.\
This triangle measures how the middle of the current bar's range relates to the middle of the frozen structure. When price drifts above the structural center, the angle turns positive; when it sinks below, the angle turns negative. Because the center sits between the ceiling and floor, this triangle tends to capture the general directional lean of price within the structure --- whether the market is favoring the upper half or the lower half of its frozen range.

[![snapshot](https://www.tradingview.com/x/NHaY5uip/)](https://www.tradingview.com/x/NHaY5uip/)

▼ Floor --- LL → Low

The Floor triangle connects the frozen lowest low to the current bar's low. Vertex A is the floor level at the freeze bar; vertex C is the current bar's low. This triangle tracks how the market's lower boundary behaves relative to the structural floor.\
When the current low is above the frozen floor, the angle is positive --- price is holding above the reference. When the low approaches the floor, the angle compresses toward zero. A negative angle would indicate a breakdown, but as with the Ceiling, a close below the floor resets the anchor.\
The Floor triangle mirrors the Ceiling triangle from the opposite direction and is useful for observing support behavior, compression near the lower boundary, or gradual lift away from the structural low.

[![snapshot](https://www.tradingview.com/x/LnN26cBx/)](https://www.tradingview.com/x/LnN26cBx/)

△ Pin Up --- HH → Upper Wick

The Pin Up triangle isolates the upper wick of the current candle relative to the frozen ceiling. Unlike the main triangles, this one uses three vertices to form a non-right triangle: vertex A is the frozen HH at the freeze bar; vertex B is the current bar's high (the tip of the upper shadow); and vertex C is the current bar's body top --- the higher of the open and close.\
The vertical side BC represents the upper wick itself. The angle at vertex A measures how much the wick fans out as seen from the frozen ceiling --- a wider angle means a longer wick relative to the time distance from the anchor. When the upper wick is zero (high equals the body top), all Pin Up readings collapse to zero.\
This triangle captures rejection behavior at the top of the candle. A long upper wick near the ceiling suggests price tested the upper zone and was pushed back. The geometric measurement of that rejection --- its angle, distance, area, and centroid --- provides a structured way to observe and quantify rejection from the upper area.

[![snapshot](https://www.tradingview.com/x/zf6C3E7w/)](https://www.tradingview.com/x/zf6C3E7w/)

▽ Pin Down --- LL → Lower Wick

The Pin Down triangle isolates the lower wick of the current candle relative to the frozen floor. It mirrors the Pin Up construction from the opposite side: vertex A is the frozen LL at the freeze bar; vertex B is the current bar's low (the tip of the lower shadow); and vertex C is the current bar's body bottom --- the lower of the open and close.\
The vertical side BC represents the lower wick itself. The angle at vertex A measures how much the lower wick fans out as seen from the frozen floor. When the lower wick is zero (low equals the body bottom), all Pin Down readings collapse to zero.\
This triangle captures rejection behavior at the bottom of the candle. A long lower wick near the floor suggests price tested the lower zone and found support. The geometric measurement helps observe rejection from the lower area or buying absorption, providing a structured complement to the Pin Up readings.

[![snapshot](https://www.tradingview.com/x/Aw2CJI4q/)](https://www.tradingview.com/x/Aw2CJI4q/)

Four Metrics per Triangle

Each of the five triangles produces four independent geometric measurements on every bar: angle, distance, area, and centroid. Together, these 20 series (4 metrics × 5 triangles) form the complete output of the ICS engine. Each metric captures a different aspect of the triangle's shape, and all are calculated in the same normalized ICS space --- vertical axis as log(price) / sigma, horizontal axis as bars / lookback --- so their values are more comparable within the same framework across different symbols, timeframes, and volatility regimes.

[![snapshot](https://www.tradingview.com/x/tqj0DSrs/)](https://www.tradingview.com/x/tqj0DSrs/)

θ Angle --- Steepness of Movement

Angle measures how steeply price has moved relative to the frozen reference, expressed in degrees.\
For the three main triangles, angle is the arctangent of the vertical displacement divided by the horizontal displacement: θ = atan(dy / dx) × 180 / π. A positive angle means the target price is above the anchor level; a negative angle means it is below. The steeper the angle, the more directional the movement relative to the time elapsed.\
For the two pin triangles, angle is measured differently. Instead of a single hypotenuse, the pin triangle has two sloped sides running from the anchor to the candle's extreme (B) and body edge (C). The angle is the difference between these two slopes as seen from vertex A: θ = (atan((yB - yA) / dx) - atan((yC - yA) / dx)) × 180 / π. This captures how much the wick fans out relative to the anchor --- a wider spread means a longer wick seen from a greater geometric distance.\
As time passes and dx increases, the angle naturally compresses even if dy stays constant. This is not a flaw --- it reflects the geometric reality that the same price displacement looks less steep when measured over a longer time base.

dy Distance --- Signed Displacement

Distance measures how far the target has moved from the anchor in ICS-normalized vertical space. It is the vertical leg of the right triangle: dy = log(targetPrice) / σ - log(anchorPrice) / σ.\
The sign tells the direction: positive means the target is above the anchor, negative means below. Because the displacement is divided by sigma (Yang-Zhang volatility), the same numeric value of dy represents the same relative stretch within the model's normalized scale. A distance of 2.0 means the target is two volatility-adjusted units above the anchor.\
For the pin triangles, distance is defined as the ICS length of the wick itself: dy = log(extremePrice) / σ - log(bodyEdge) / σ. This isolates the shadow's reach in normalized space --- how far the wick extended beyond the real body.

A Area --- Combined Displacement

Area combines both time and price displacement into a single reading: A = 0.5 × |dy| × |dx|. It is always zero or positive.\
Because area is the product of two dimensions, it grows when either dimension grows. A triangle with a large price move over a short time can have the same area as a triangle with a small price move over a long time. This makes area useful for assessing the overall weight of a move --- how much geometric space the triangle occupies, regardless of whether it came from sharp movement or gradual accumulation.\
Area often expands as a move extends over time. With each new bar, dx increases, so even if dy remains unchanged, the triangle's area grows. A shrinking area within an active anchor cycle means dy is compressing faster than dx is expanding --- the move is losing geometric weight.\
For the pin triangles, the same formula applies. Because both vertices B and C sit on the current bar (same x-coordinate), the shoelace formula reduces exactly to 0.5 × |dy| × |dx|, where dy is the wick length in ICS space.

C̄ Centroid --- Geometric Balance Point

Centroid is the y-coordinate of the triangle's geometric center of mass, measured in ICS space.\
For the three main triangles, the centroid formula is C̄ = (2 - yA + yC) / 3, where yA is the anchor's ICS position and yC is the target's ICS position. The anchor vertex carries twice the weight because it serves as the shared corner of both the horizontal and vertical legs --- geometrically, the balance point of a right triangle sits one-third of the way from the right-angle vertex toward the hypotenuse.\
For the two pin triangles, all three vertices contribute equally: C̄ = (yA + yB + yC) / 3. This is the standard centroid formula for a general triangle.\
As the triangle's shape changes, the centroid shifts. When the target moves further from the anchor, the centroid drifts in that direction. The centroid does not measure speed or size --- it tracks where the geometric weight of the triangle is concentrated. Shifts in centroid can help highlight changes in the structural balance before they become visible in angle or distance alone.\
Together, these four metrics translate each triangle into a set of continuous, normalized readings that evolve with every bar. Angle captures direction and steepness; distance captures reach; area captures accumulated weight; and centroid captures balance. The strategy makes all 20 series available for condition testing through its configurable slot system.

The 20 Geometric Lenses

So far the framework has been built piece by piece: the Introduction set out the geometric idea, the ICS Coordinate Framework made both axes dimensionless, the Frozen Anchors fixed a stable origin, the Five Triangle Types defined what each shape measures, and the Four Metrics per Triangle turned each shape into angle, distance, area, and centroid.\
Putting those together gives twenty distinct readings --- four metrics across five triangles. We will call these the 20 Geometric Lenses. Each lens is a single metric applied to a single triangle, and together they let the trader act as a pure observer: rather than predicting, the trader watches how the geometric behavior of the triangle data unfolds next to the price chart, lens by lens.\
All twenty lenses are plotted in a separate pane beneath the price chart. What appears there is the raw geometric output --- nothing is smoothed, rescaled, or reshaped after the fact. Every value is exactly what the triangle produced inside the ICS framework: the angle as it was measured, the distance, the area, the centroid, each plotted directly. The lower pane is therefore a transparent window onto the geometry itself, not a filtered or cosmetic version of it. Several of these readings behave like oscillators --- the angles, for instance, stay within a bounded range and swing across a zero line --- while others, such as area, accumulate and reset with each anchor cycle. The pane reads like an oscillator panel, but its real purpose is to expose the unaltered measurements for direct observation.\
We will go through all twenty in order, beginning with the Ceiling triangle.

*The observations presented in this section are those of the strategy's publisher. One of the defining features of this framework is that the same geometric data can lead to different readings for different observers. Because the twenty lenses display raw, unaltered measurements --- with no built-in interpretation or directional bias --- each trader is free to develop their own observations, identify their own patterns, and draw their own conclusions from what the geometry reveals. What follows is one set of observations, not the only set.*

1\. Ceiling Angle

The Ceiling Angle tracks the ICS angle between the frozen ceiling and the current bar's high. The reading is negative when the high sits below the ceiling level and moves into positive territory when the high extends above it. As each new bar arrives, the angle evolves continuously. When the anchor resets, the measurement cycle restarts from the new reference.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/oPMjW3id/)](https://www.tradingview.com/x/oPMjW3id/)\
IMAGE CAPTION:\
Ceiling Angle on a SOLUSD daily chart. The lower pane displays the raw Ceiling Angle reading across multiple anchor cycles. The angle moves within a negative range for extended periods. When the reading reaches toward the boundary of that range, notable changes in price behavior are visible at the corresponding points on the chart (×). Each anchor reset starts a new cycle, and the measurement recalculates from the new reference.

2\. Ceiling Distance

The Ceiling Distance measures the signed displacement between the frozen ceiling and the current bar's high in ICS space. The reading is negative when the high sits below the ceiling level and moves toward zero or positive when the high approaches or extends above it.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/4Exb3d4E/)](https://www.tradingview.com/x/4Exb3d4E/)\
IMAGE CAPTION:\
Ceiling Distance on an AAPL daily chart. The lower pane displays the raw Ceiling Distance reading across multiple anchor cycles. The distance moves within a negative range for extended periods. When the reading reaches toward the boundary of that range, notable changes in price behavior are visible at the corresponding points on the chart (×). Each anchor reset starts a new cycle, and the measurement recalculates from the new reference.

3\. Ceiling Area

The Ceiling Area combines the time and price displacement of the Ceiling triangle into a single non-negative reading. As the anchor cycle progresses, the area evolves with each new bar --- expanding when the triangle grows in either dimension and contracting when the vertical displacement narrows faster than the horizontal extends.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/MRgXSjcF/)](https://www.tradingview.com/x/MRgXSjcF/)\
IMAGE CAPTION:\
Ceiling Area on daily chart. The lower pane displays the raw Ceiling Area reading within an anchor cycle. The area builds gradually as the cycle progresses and contracts when the vertical displacement narrows. Changes in the direction of the area reading correspond to visible shifts in price behavior on the chart above.

4\. Ceiling Centroid

The Ceiling Centroid tracks the geometric balance point of the Ceiling triangle in ICS space. As the triangle's shape changes, the centroid shifts --- reflecting where the geometric weight of the triangle sits between the frozen ceiling and the current bar's high.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/zYMmvcdi/)](https://www.tradingview.com/x/zYMmvcdi/)\
IMAGE CAPTION:\
Ceiling Centroid on a daily chart. The lower pane displays the raw Ceiling Centroid reading. The centroid reaches the zero level at two separate points within the same period. At the first, price closed higher afterward; at the second, price closed lower --- two different outcomes from the same numeric level in the geometric data.

5\. Center Angle

The Center Angle measures the angle between the frozen center and the current bar's midpoint in ICS space, with each level taken as a geometric mean. The reading moves above zero when the current midpoint sits above the structural center and below zero when it sits beneath it.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/K5k0Zdnt/)](https://www.tradingview.com/x/K5k0Zdnt/)\
IMAGE CAPTION:\
Center Angle on a daily chart. The lower pane displays the raw Center Angle reading, which crosses the zero line as the current midpoint moves above or below the structural center. When the reading reaches toward the upper boundary of its range (shaded zone), notable changes in price behavior are visible at the corresponding points on the chart.

*Reading Lenses Together\
The patterns shown so far were drawn from the lenses of the Ceiling triangle, taken one at a time. Each lens --- angle, distance, area, centroid --- was read on its own, in isolation, so that its individual behavior could be observed clearly.\
From this point forward, the focus shifts to a second layer of observation: reading the lenses in combination. A single lens describes one geometric relationship. When two or more lenses are placed on the same pane and read together, their interaction --- whether they move in agreement, diverge, converge toward a shared level, or cross --- adds a dimension that no single lens reveals on its own. The same raw data is still displayed without alteration; only now it is observed as a set of relationships rather than as separate lines.\
The image below places two lenses on the same pane: the Ceiling Angle and the Center Angle. Read individually, each traces its own path within the bounds of its range. Read together, the points where the two converge toward the same level, or where one turns while the other holds, form a combined reading. As marked on the chart, these moments of interaction align with notable shifts in price behavior above.*

[![snapshot](https://www.tradingview.com/x/QbJnTpzl/)](https://www.tradingview.com/x/QbJnTpzl/)\
IMAGE CAPTION:\
Ceiling Angle (red) and Center Angle (cyan) read together on a daily chart. Each lens traces its own path within its range. The marked points show where the two readings interact --- converging toward a shared level or turning at the same time --- and these moments align with notable shifts in price behavior on the chart above.

6\. Center Distance

The Center Distance measures the signed displacement between the frozen center and the current bar's midpoint in ICS space. The reading moves above zero when the current midpoint sits above the structural center and below zero when it sits beneath it, with the magnitude showing how far the midpoint has stretched from the center.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/q8KIAynL/)](https://www.tradingview.com/x/q8KIAynL/)\
IMAGE CAPTION:\
Center Distance (cyan) and Ceiling Distance (red) read together on a daily chart. Each lens measures how far price has displaced from its own reference level --- the center and the ceiling. Placing them on the same pane shows the displacement from both anchors simultaneously. The marked points highlight where the relationship between these two displacements shifts, and these moments align with notable changes in price behavior on the chart above.

7\. Center Area

The Center Area combines the time and price displacement of the Center triangle into a single non-negative reading. As the anchor cycle progresses, the area evolves with each new bar --- expanding when the triangle grows in either dimension and contracting when the vertical displacement narrows faster than the horizontal extends.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/lt97G4bM/)](https://www.tradingview.com/x/lt97G4bM/)

IMAGE CAPTION:\
Center Area on a daily chart. The lower pane displays the raw Center Area reading within an anchor cycle. The area builds gradually as the cycle progresses, reaching a peak before contracting. The marked points show where changes in the direction of the area reading correspond to visible shifts in price behavior on the chart above.

8\. Center Centroid

The Center Centroid tracks the geometric balance point of the Center triangle in ICS space. It measures where the triangle's internal weight is concentrated between the frozen center and the current bar's midpoint.\
Unlike Center Distance, which shows how far the midpoint has moved from the frozen center, the centroid shows the balance position created by that movement. When the current midpoint holds above the frozen center, the centroid tends to remain elevated. When the anchor cycle changes, the centroid drops sharply and restarts from a new balance zone. Within an active cycle, compression back toward the center produces a gradual drift rather than a sudden collapse.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/TUQY7sDr/)](https://www.tradingview.com/x/TUQY7sDr/)\
IMAGE CAPTION:\
Center Centroid on a daily chart. The upper chart shows the frozen Ceiling, Center, and Floor levels, while the lower pane displays the raw Center Centroid reading. The centroid line remains relatively stable while price develops inside the active structure, then drops sharply at marked points where the anchor cycle resets and the geometric balance restarts from a new level. These sudden collapses are not smoothed signals; they are direct changes in the raw centroid measurement produced by the Center triangle.

9\. Floor Angle

The Floor Angle measures the slope between the frozen floor and the current bar's low inside the ICS framework. It shows how the lower edge of price is positioned relative to the structural floor after time and volatility normalization.\
This lens is mainly about lower-boundary behavior. When the current low stays well above the frozen floor, the angle remains positive, showing that price is holding above the lower reference. As the low moves closer to the floor, the angle compresses toward zero. If the structure breaks and the anchor cycle reset, the reading can collapse and begin again with a new reference.\
In the image below, the Floor Angle line stays mostly positive while price remains above the frozen floor. The sharp drops marked on the oscillator are not ordinary bearish signals by themselves. They mainly show moments where the active structure ends and the geometric measurement restarts from a fresh anchor.

[![snapshot](https://www.tradingview.com/x/1jLD3qbg/)](https://www.tradingview.com/x/1jLD3qbg/)\
Image caption:\
Floor Angle on a daily chart. The upper chart shows the frozen Ceiling, Center, and Floor levels, while the lower pane displays the raw Floor Angle reading. The angle stays positive while the current lows remain above the frozen floor. At the marked points, the reading drops sharply as the anchor cycle resets, and the floor relationship is recalculated from a new structural base. This lens helps observe whether the market is lifting away from the lower boundary, compressing toward it, or starting a new measurement cycle.

10\. Floor Distance

Floor Distance measures the vertical separation between the frozen floor and the current bar's low in ICS-normalized space. While Floor Angle describes the slope of that relationship over time, Floor Distance focuses only on how far the current low is standing above, near, or potentially below the structural floor.\
When the current low remains clearly above the frozen floor, the distance reading stays positive. A larger value means the lower edge of price has moved farther away from the floor. A smaller value means price is pressing closer to the lower boundary. If the anchor cycle resets, the measurement restarts from the new floor reference, which can create sudden drops in the oscillator.\
This lens is useful because it removes the time-slope component and isolates the lower-side displacement itself. Floor Angle may gradually compress as more bars pass, but Floor Distance is more directly tied to the vertical relationship between the current low and the frozen floor. For this reason, the two lenses often share the same reset points, but they do not always tell the same story between resets.

[![snapshot](https://www.tradingview.com/x/L1ea8ywt/)](https://www.tradingview.com/x/L1ea8ywt/)

Image caption:\
Floor Distance on a daily chart, shown together with Floor Angle for comparison. Both readings come from the same Floor triangle and use the current bar's low relative to the frozen floor. Their sharp reset points often align because both measurements restart when the anchor cycle changes. The key difference is that Floor Angle expresses the relationship as a time-based slope, while Floor Distance shows the raw vertical separation in ICS space. In the lower pane, the distance line highlights how close or far the current lows are from the structural floor, independent of the angle's time-compression behavior.

11\. Floor Area

Floor Area tracks the geometric footprint of the Floor triangle as both time and lower-side displacement accumulate within an anchor cycle.\
In this image, Floor Area is shown alongside Ceiling Area on the same pane. Both lenses measure geometric expansion, but from opposite reference levels --- one from the frozen floor, the other from the frozen ceiling. When the two area readings grow together, both the upper and lower triangles are expanding simultaneously, and the structure is developing geometric weight on both sides. When one grows while the other stays flat or contracts, only one side of the structure is accumulating. The relationship between the two --- whether they expand in parallel, diverge, or one leads to the other --- forms a combined observation that neither area line shows on its own.\
The circled zones mark where both areas begin to rise from a low base, and the curved arrows trace their parallel expansion as price moves away from the floor region.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/r0DoJBkC/)](https://www.tradingview.com/x/r0DoJBkC/)

IMAGE CAPTION:\
Floor Area (cyan) and Ceiling Area (red) read together on a daily chart. Both lenses track geometric expansion from opposite reference levels --- the frozen floor and the frozen ceiling. The circled zones mark where both readings begin to rise, and the curved arrows trace their parallel expansion. Reading the two areas together shows whether geometric weight is building on one side of the structure or on both simultaneously.

12\. Floor Centroid

Floor Centroid locates the geometric balance point of the Floor triangle in ICS space. Rather than measuring pure displacement from the frozen floor, it shows where the triangle's internal balance sits as time and lower-side price movement develop within the active anchor cycle.\
For the main triangles, the centroid is not placed halfway between anchor and target. It is weighted toward the frozen anchor, so it responds more slowly than raw distance. In practical terms, this makes Floor Centroid a steadier reading: when the current lows lift away from the floor, the centroid rises gradually; when price compresses back toward the floor within the same cycle, it drifts lower rather than collapsing. Sharp drops occur when the anchor cycle resets, not from ordinary compression.\
In this image, Floor Centroid is shown together with Center Centroid and Ceiling Centroid, while the three triangles themselves are drawn on the price chart above. This combined view matters. Floor Centroid gives the lower triangle's balance point, but when it is read beside the other two centroids, it becomes part of a structural map. The three centroid lines remain closely grouped and broadly parallel, reflecting the relatively narrow spread of the current frozen structure. Their vertical ordering also mirrors the structure itself: Ceiling Centroid sits highest, Center Centroid stays between them, and Floor Centroid remains lowest.\
This is the added value of reading lenses in combination. Floor Centroid alone tells where the lower triangle's balance is located. Read together with the center and ceiling centroids, it also shows how balance is distributed across the whole structure --- whether the three geometric centers are moving in alignment, spreading apart, or resetting together into a new cycle.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/JJ7jPVvd/)](https://www.tradingview.com/x/JJ7jPVvd/)\
IMAGE CAPTION:\
Floor Centroid (teal) read together with Center Centroid (cyan) and Ceiling Centroid (red) on a daily chart. The upper panel shows the three main triangles drawn from the frozen floor, center, and ceiling to the current bar, while the lower pane displays their centroid readings. The three lines remain tightly clustered and broadly parallel, reflecting the relatively narrow spread of the current frozen structure. The marked drops occur when the anchor resets, after which all centroid readings restart from the new structural framework. Reading the three centroids together gives a fuller view of how geometric balance is distributed across the entire structure.

13\. Pin Up Angle

Pin Up Angle measures how much the current bar's upper wick fans out as seen from the frozen ceiling. The reading stays near zero on bars with little or no upper shadow and spikes sharply when a candle prints a notable wick near the ceiling zone.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/4HQUXKin/)](https://www.tradingview.com/x/4HQUXKin/)

IMAGE CAPTION:\
Pin Up Angle on a daily chart. Unlike the main triangle lenses, which produce continuous evolving lines, this reading is pulse-like --- flat near zero most of the time, then spiking on individual bars where the upper wick is geometrically significant relative to the frozen ceiling. The marked candles on the price chart show where those spikes originate.

14\. Pin Up Distance

Pin Up Distance measures the ICS-normalized length of the upper wick itself --- the vertical gap between the bar's high and the top of its real body. Most bars produce small wicks, so the reading spends the majority of its time in a narrow low range near zero. Occasionally, a bar prints a wick long enough to push the reading into an upper zone that is rarely visited. These rare excursions are infrequent, but the moments they mark on the price chart tend to stand out.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/ivFJC2Om/)](https://www.tradingview.com/x/ivFJC2Om/)\
IMAGE CAPTION:\
Pin Up Distance on a daily chart. The lower pane shows the reading confined to a low range on most bars. The shaded upper zone marks a numeric region that is seldom reached. When the reading enters that zone (×), the corresponding candles on the price chart carry notably long upper shadows near the frozen ceiling --- rare geometric events within the wick data.

15\. Pin Up Area

Pin Up Area tracks the geometric footprint of the upper wick triangle. Because it multiplies the wick's ICS length by the normalized time distance from the anchor, it responds not only to how long the wick is but also to when within the anchor cycle it appears.\
One pattern worth noting is what happens when Pin Up Area stays flat near zero for an extended stretch. When the reading settles into a quiet, non-varying floor, it means that bar after bar, the market is producing little to no upper shadow. This sustained absence of upper-wick activity --- visible as a flat line hugging zero --- often coincides with a clean directional move on the price chart. The geometry is not signaling anything; it is simply not registering upper-side rejection, and that silence itself becomes observable.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/FuW3nW6V/)](https://www.tradingview.com/x/FuW3nW6V/)\
IMAGE CAPTION:\
Pin Up Area on a 4-hour chart. Earlier in the chart, volatile price action produces sporadic spikes in Pin Up Area as candles print significant upper wicks. As price transitions into a sustained move downward from the ceiling region, the reading flattens near zero and stays there --- bar after bar producing no meaningful upper shadow. The arrow traces this quiet stretch alongside the corresponding decline on the price chart. The flat reading is not a lack of data; it is the geometric signature of a move where upper-wick rejection has gone silent.

16\. Pin Up Centroid

Pin Up Centroid tracks the geometric balance point of the upper wick triangle --- the average ICS position of all three vertices: the frozen ceiling, the bar's high, and the top of the real body. When the upper wick is absent or minimal, the centroid holds a steady flat level. When a bar prints a notable upper shadow, the centroid shifts briefly before returning.\
In the publisher's observation, when the centroid line runs flat during a sustained move, the brief pulses that break away from that flat level mark individual bars where the wick geometry changed. Within a defined trend, these pulses can highlight potential profit-taking points --- moments where the upper-shadow structure briefly departs from the trend's otherwise quiet wick profile. As noted earlier, this is the publisher's reading; other observers may interpret the same pulses differently.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/jlOga5nf/)](https://www.tradingview.com/x/jlOga5nf/)\
IMAGE CAPTION:\
Pin Up Centroid on a 1-hour chart during a sustained decline. The centroid holds a flat level while price trends lower with minimal upper shadows. The marked pulses show brief departures from that flat line --- individual bars where the upper wick triangle's balance shifted. In the publisher's view, these pulses within an otherwise quiet centroid can serve as observable points of interest along the trend.

17\. Pin Down Angle

Pin Down Angle measures how much the current bar's lower wick fans out as seen from the frozen floor --- the mirror of Pin Up Angle viewed from the opposite side. The reading sits near zero on bars with little or no lower shadow and drops into deep negative territory when a candle prints a significant lower wick. These spikes are rare, single-bar events, and their depth can be substantial.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/QflCQJNz/)](https://www.tradingview.com/x/QflCQJNz/)\
IMAGE CAPTION:\
Pin Down Angle on a daily chart. The reading holds a flat band near zero across most of the chart. The circled zones on the price chart highlight clusters of bars carrying long lower shadows, and the arrows below point to the corresponding deep negative spikes in the oscillator --- reaching as far as -80 to -90. Over roughly eighteen months, only a few such spikes appear, making each one a geometrically rare event in the lower-wick data.

18\. Pin Down Distance

Pin Down Distance measures the ICS-normalized length of the lower wick --- the vertical gap between the bar's low and the bottom of the real body. Unlike Pin Down Angle, which sits flat most of the time and fires rare deep spikes, this lens oscillates continuously because nearly every bar carries some degree of lower shadow. The reading produces a constant rhythm of small negative values.\
Within that steady oscillation, the observation lies in identifying the breaks --- the moments when the reading drops well beyond its normal range into unexpectedly deep territory. These outlier swings mark bars where the lower wick was abnormally long relative to the prevailing rhythm. They are few, but each one stands out clearly against the baseline noise.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/cFonGGk7/)](https://www.tradingview.com/x/cFonGGk7/)

IMAGE CAPTION:\
Pin Down Distance on a daily chart. The lower pane shows a continuously oscillating reading --- the normal rhythm of lower-wick lengths bar after bar. The shaded zone marks a deeper range that the reading seldom enters. The (×) points identify the moments where the oscillation breaks below its usual boundary and reaches into that zone, and the corresponding bars on the price chart carry notably long lower shadows at key points along the decline.

19\. Pin Down Area

Pin Down Area tracks the geometric footprint of the lower wick triangle. Not every lens produces a clear standalone pattern, and in the publisher's observation, Pin Down Area is one of those: read alone, it tends to stay close to zero without forming easily distinguishable structures.\
Where it becomes observable is in combination --- specifically, when read alongside Floor Area on the same pane. Both lenses share the same time axis from the anchor, but they measure different vertical components: Floor Area measures how far the current low stands from the frozen floor, while Pin Down Area measures the wick length at the bottom of each bar. When Floor Area contracts toward Pin Down Area and the two converge, it means that the floor displacement has compressed to the point where it is comparable to the wick size itself --- the structure is squeezed near the floor. In this image, such a convergence aligns with a visible shift in price behavior.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/IIYXkkcl/)](https://www.tradingview.com/x/IIYXkkcl/)\
IMAGE CAPTION:\
Pin Down Area (purple) shown alongside Floor Area (teal) on a 4-hour chart. Pin Down Area stays near zero throughout, offering little standalone structure. The (×) marks and the arrow trace the stretch where Floor Area declines toward Pin Down Area as price moves closer to the frozen floor. At the point of convergence, a shift in price behavior is visible on the chart above --- an example of a lens that gains its meaning primarily through combination rather than in isolation.

20\. Pin Down Centroid

Pin Down Centroid tracks the geometric balance point of the lower wick triangle --- the average ICS position of the frozen floor, the bar's low, and the bottom of the real body.\
In the publisher's observation, the pulse pattern produced by this centroid captures the rhythm of the market in a distinctive way. Each sharp pulse in the reading corresponds to a jump on the price chart --- a moment where the lower-wick geometry shifted abruptly. The sequence of these pulses, their spacing, and their amplitude together form a visual imprint of how the market moves in discrete steps rather than smooth curves. As with all observations in this section, other observers looking at the same data may identify a different rhythm or read the pulses through a different lens.\
See the pattern formed in the image below.

[![snapshot](https://www.tradingview.com/x/bwzjFSBT/)](https://www.tradingview.com/x/bwzjFSBT/)\
IMAGE CAPTION:\
Pin Down Centroid on a 4-hour chart. The lower pane displays the centroid reading as price transitions from a flat base into a sharp upward move. Each pulse in the centroid line aligns with a discrete jump on the price chart, tracing the step-by-step rhythm of the advance. The arrows mark the parallel between the two: as price leaps, the centroid pulses --- a geometric mirror of the market's own cadence.

From Observation to Combinatorial Reality

Twenty lenses have now been laid out --- each one a single geometric measurement from a single triangle, plotted without alteration. As the previous sections showed, reading them individually reveals one layer, and reading them in combination reveals another. But how large is the space of possible combinations?\
If the question is simply which lenses to display --- which lines to turn on in the oscillator pane --- then the answer is a straightforward combinatorial one. Each of the twenty lenses is either on or off, giving 2²⁰ - 1 = 1,048,575 non-empty subsets. Over one million ways to observe. But this number, while large, is generic. Any set of twenty items produces the same count. It does not yet reflect what makes this framework different.\
What makes space real is the step from observation to action. This strategy includes a configurable slot system --- twenty independent condition slots, each of which transforms a passive lens into an active rule. When a slot is activated, three choices are made:\
Which of the 20 geometric lenses these slot monitors. Conditioning how the value is evaluated: above a threshold, below it, between two bounds, or crossing in either direction. Five options. Side --- what the rule applies to: long entry, short entry, both entries, long exit, short exit, both exits, or all. Seven options.\
A single active slot therefore has:\
20 × 5 × 7 = 700 structural configurations\
This number is already specific to this framework --- it comes from geometry, not from a textbook formula. And it grows fast. When two slots are active simultaneously, the number of distinct rule pairs rises to 245,350. Three active slots produce over 57 million. Five active slots: over 1.4 trillion.

1 active slot → 700\
2 active slots → 245,350\
3 active slots → 57,411,900\
4 active slots → 10,090,141,425\
5 active slots → 1,420,691,912,640

And this is only the structural count --- the skeleton of variable, condition, and side. Each slot also carries a numeric threshold: the specific level at which the condition fires. The threshold is a continuous parameter. It is not selected from a list; it can be of any value. This means every one of the 700 structural configurations branches into a continuous range of possibilities. The number above is not the full space --- it is the floor.\
With all twenty slots available, the raw configuration space reaches approximately 10³⁹ structural combinations --- a thirty-nine-digit number. For perspective, the number of seconds since the Big Bang is roughly 4.3 × 10¹⁷, a number with eighteen digits. The full configuration space of this strategy, using only its built-in geometric variables and before any threshold tuning, is over a sextillion time larger than the age of the universe measured in seconds.\
Where Human Exploration Reaches Its Limit\
This is the point that is easy to underestimate. A trader looking at a chart sees patterns, draws conclusions, and builds intuition over time. But the act of combining geometric conditions --- choosing which lenses to activate, under what thresholds, on which side of the market, and how many must agree before a signal fires --- is a combinatorial task. The human mind is remarkably good at pattern recognition, but it is not built to systematically explore a space measured in tens of trillions of possibilities.\
This is what makes trading complex at a level that is rarely discussed. It is not that the individual tools are hard to understand --- each lens, each condition, each threshold is simple on its own. The complexity lives in combinations. And that complexity exists whether a trader acknowledges it. Every time a strategy is configured by hand, the trader is selecting one point in a vast space and hoping it is a good one, without visibility into what the rest of the space looks like.

AI as the Bridge

This is where artificial intelligence changes the equation. Not by replacing the trader's judgment, but by navigating the combinatorial space that no human can explore manually.\
TradingView has introduced the AI Chart Copilot:

[tradingview.com/blog/en/tradingview-ai-chart-copilot-beta-57730/](https://www.tradingview.com/blog/en/tradingview-ai-chart-copilot-beta-57730/)

An AI-powered assistant that works directly alongside your charts in the browser. It reads your current chart state, understands the indicators applied to it, and responds to natural-language questions about what it sees. Copilot is currently available in public beta for all TradingView users through a Chrome extension:

[chromewebstore.google.com/detail/tradingview-remix-ai-char/fchmejnoncmdhlebgdgifdnehoibalnd](https://chromewebstore.google.com/detail/tradingview-remix-ai-char/fchmejnoncmdhlebgdgifdnehoibalnd)

That also works in other Chromium-based browsers such as Edge, Brave, Opera, and Vivaldi.\
In the context of this strategy, the workflow becomes direct. You have twenty geometric keys in front of you. You want to know how a specific combination behaves --- say, which lenses help identify long entry conditions on a particular symbol and timeframe. Instead of manually testing hundreds of configurations, you activate the variables you want to explore in the strategy's settings panel and then ask the Copilot to analyze the result. The AI reads the chart, sees the indicator output, and helps you interpret what the geometry is showing. This turns a combinatorial search into a guided conversation.\
The twenty slots, the five conditions, the seven sides, and the continuous thresholds are all accessible through the strategy's input panel --- no code editing required. The Copilot does not replace the need to understand what each lens measures. But once that understanding is in place, it dramatically reduces the time between a question and an answer. What would take hours of manual configuration and visual comparison can become a single prompt.\
How to evaluate and act on the results --- what to look for in the output, how to read the strategy tester, and how to refine configurations from there --- is covered in the sections that follow.

Practical Notes for Deeper Review, AI as the Bridge

Copilot can read the chart directly inside the browser, including the live visual output of the strategy. This makes it useful for quick exploration questions, chart-based observation, and immediate interpretation of the active lenses.\
For a more structured review, the same lens data can also be exported from TradingView as a CSV file. When this strategy is applied to a chart, each enabled lens can appear as a named data column in the exported file, alongside the timestamp and price data.\
The important detail is that only active lenses are exported. If a lens is turned off in the strategy settings, it does not plot, and therefore it will not appear as a visible data column in the CSV. Before exporting, activate the specific lens or lenses you want to review.\
For cleaner pattern extraction, it is usually better to start with one lens per review pass. Activating all twenty lenses at once can create a dense dataset, which may be useful later but can make the first analysis harder to interpret. A focused export gives a clearer view of how one geometric series behaves across time, anchor cycles, price swings, and market structure.\
For example, the trader may activate only Pin Up Angle, export the CSV, and study how that single lens behaves near local highs, rejection zones, or failed breakouts. Then the same process can be repeated with Pin Down Angle, Center Distance, Floor Area, or any other lens.

A practical workflow is simple:

Activate one lens, export the chart data, review that lens as a numeric series, compare the findings back against the chart, and then repeat the process with another lens. Later, selected lenses can be combined if their individual behavior shows meaningful structure.\
For each lens, useful questions include: Where does this lens spend most of its time? Which numeric zones are rare? What tends to happen after the lens reaches an extreme zone?\
Does the behavior change across different anchor cycles? Does it behave differently near the ceiling, center, or floor?\
The goal is not to force a signal from every lens. Some lenses may be more useful on certain symbols, timeframes, or market regimes than others. CSV-based review simply makes those differences easier to observe in a structured way.\
Both paths use the same framework. Copilot offers a faster, chart-based way to explore the active lenses inside the browser. CSV export turns the same active lens readings into portable numerical data for deeper review. The strategy produces twenty geometric lenses; the trader chooses how to explore them.

Turning Lenses into Rules

Up to this point, the twenty geometric lenses have been presented as observation tools --- continuous readings that the trader watches, compares, and interprets visually. From this section forward, the focus shifts to action: how those same readings become the building blocks of a rule-based trading system.\
The strategy includes a configurable engine that sits between the geometric output and the order execution. It does not impose a fixed formula. Instead, it provides twenty independent condition slots, a quorum-based signal logic, and a set of position management tools. The trader decides which lenses to monitor, what conditions to set, how many must agree before a signal fires, and how the resulting positions are managed. Every parameter is accessible through the strategy's settings panel --- no code editing is required.

Condition Slots

The strategy provides twenty condition slots. Each slot is an independent rule that can be configured to monitor any one of the twenty geometric lenses and test whether its current value meets a specified condition.\
Each slot has five configurable settings:\
Variable selects which of the twenty lenses this slot watches. When set to OFF, the slot is inactive and does not participate in signal logic. The available variables match the plot labels in the oscillator pane: Ceil angle, Ceil distance, Ceil area, Ceil centroid, Ctr angle, Ctr distance, Ctr area, Ctr centroid, Flr angle, Flr distance, Flr area, Flr centroid, PnU angle, PnU distance, PnU area, PnU centroid, PnD angle, PnD distance, PnD area, PnD centroid.\
Condition defines how the selected value is evaluated. Five options are available: > (above) means the current value must exceed the threshold; < (below) means it must be under the threshold; between means it must fall within the threshold and an upper bound; cross > means the value must cross above the threshold on the current bar; and cross < means it must cross below.\
Threshold is the numeric level against which the condition is tested. For the between condition, a second field --- Upper bound --- sets the upper boundary of the range.\
Apply to determines which side of the strategy this slot feeds into. Seven options are available: Long entry, Short entry, Both entry, Long exit, Short exit, Both exit, and All. This means the same geometric lens can serve as an entry filter on one slot and an exit trigger on another, or the same condition can apply across all signal types at once.\
A slot set to OFF is completely excluded from all calculations. It does not count as active, does not affect the quorum, and does not block or contribute to any signal. This allows the trader to start with just one or two active slots and expand gradually as observations develop into tested rules.

Quorum Logic

Once the condition slots are configured, the strategy needs a rule for combining them into a signal. This is controlled by a single setting: Minimum slots required.\
On every bar, the strategy counts how many active slots apply to each signal side (long entry, short entry, long exit, short exit) and how many of those currently pass their condition. A signal fires when the number of passing slots reaches or exceeds the minimum required --- or the total number of active slots for that side, whichever is smaller.\
This single setting creates a flexible spectrum between two extremes.\
When Minimum slots required is set to 1, any single passing slot is enough to trigger a signal. This is equivalent to OR logic --- if any one condition is met, the signal fires. This is the most permissive setting and will generate the most frequent signals.\
When Minimum slots required equals the total number of active slots for that side, every slot must pass its condition simultaneously. This is equivalent to AND logic --- all conditions must align on the same bar. This is the most restrictive setting and will generate the fewest signals.\
Any value in between creates a quorum --- a majority or partial consensus filter. For example, if five slots are active for long entry and the minimum is set to 3, the signal fires when at least three of the five conditions are met on the same bar. It does not matter which three pass; the strategy counts the number of passes, not specific slot identities.\
This design gives the trader direct control over how strict or permissive the signal filter is, without changing any individual slot condition. The same five slots can produce very different signal profiles simply by adjusting the quorum threshold from 1 to 5.\
One safeguard is built into the entry logic: if both the long entry and short entry quorums are met on the same bar, neither trade is executed. This conflict guard prevents entry when the geometric data supports both directions simultaneously --- a condition that reflects market indecision rather than a clear directional signal.\
The strategy offers two signal modes: Close and Live. In Close mode, all geometric calculations use the previous bar's confirmed data until the current bar fully closes. Signals only appear after a bar is complete --- what appears on the chart is final and will not change. This is the recommended starting point, especially for backtesting, because it eliminates the possibility of a signal appearing mid-bar and then disappearing before the close. In Live mode, calculations update in real time using the current bar's data as it forms. This produces faster readings, but any signal that appears while the bar is still open may shift or vanish before the bar closes. The choice between the two does not change the geometric framework --- it only determines when within each bar the measurements are taken.\
The condition slots are not limited to entries. Each slot's Apply to setting includes exit options --- Long exit, Short exit, both exit, and All --- which means the same quorum logic that governs entry signals also governs formula-based exits. When enough exit-side slots pass their conditions on the same bar, the strategy closes the corresponding position. This gives the trader a symmetric system: entries and exits are both built from geometric conditions, tested against the same quorum threshold, and fully configurable through the settings panel. A new entry is only executed when no position is currently open --- the strategy does not add to or reverse an existing position through the entry signal.

Position Management

Once a position is open, the strategy provides three optional tools for managing it: a fixed stop-loss, a fixed take-profit, and a trailing stop. Each can be enabled or disabled independently, and all three can run at the same time.\
Stop-loss and take-profit are defined as percentages. The stop-loss is placed at a fixed distance below the entry price for long positions, or above it for short positions. The take-profit mirrors this from the opposite side. Both levels are calculated from the actual average entry price --- the price at which the position was filled --- not from the close of the signal bar. This distinction matters in live trading, where the fill price and the bar's close are rarely identical.\
The trailing stop tracks the best price reached since entry. For a long position, it follows the highest high and places a dynamic stop at a fixed percentage below that peak. For a short position, it follows the lowest low and places the stop above that trough. The trail only moves in the trader's favor --- it never pulls back. When both a fixed stop-loss and a trailing stop are active on the same position, the strategy automatically selects the more protective level: the higher of the two for longs, the lower for shorts. A single exit order is maintained at all times, so there is no conflict between mechanisms. Whichever level is hit first --- stop-loss, take-profit, or trailing stop --- closes the position.\
The strategy also includes an alert system. Alerts can be enabled separately for long entries, short entries, long exits, and short exits. Each alert message includes the symbol, timeframe, quorum result, and --- optionally --- the full list of active slot values and the calculated SL/TP levels. This allows the trader to receive structured notifications without needing to watch the chart continuously.

Settings Overview

Every parameter described in this publication is accessible through the strategy's settings panel. No code editing is needed. Each setting includes a tooltip that explains its purpose and behavior. The panel is organized into the following groups:

Calculation

Signal mode (Close or Live).

Triangle System

Lookback period --- the number of bars used to establish the frozen anchors.\
▲ Ceiling - ◆ Center - ▼ Floor - △ Pin Up - ▽ Pin Down\
Each of the five triangle groups has four lens toggles (Angle, Distance, Area, Centroid) and a color picker. Enabling a lens activates its plot in the oscillator pane and makes its data available for condition slots and CSV export.

Chart Overlay

Anchor lines toggle, label size, and individual triangle overlay toggles for all five triangle types. Purely visual --- does not affect signals or calculations.

⚡ Slot 1 through Slot 20

Twenty independent condition slots. Each slot: Variable, Condition, Threshold, Upper bound (for between), and Apply to.

⚙️ Signal Logic

Minimum slots required --- the quorum threshold that controls how many active slots must pass before a signal fires.

📊 Position Management

Enable stop-loss and its percentage, enable take-profit and its percentage, trailing stop toggle and trail percentage.

🔔 Alerts

Separate toggles for long entry, short entry, long exit, and short exit alerts. Options to include slot details and SL/TP levels in the alert message.

*A Note from the Publisher

This strategy began with a simple question:

what if we could measure what we see on a chart --- not with lines drawn by hand, but with geometry that holds its structure across different symbols, timeframes, and chart scales?

As traders, our eyes live on charts. We read shapes, trace structures, and look for patterns --- often without realizing that what we see can depend on how the chart is displayed. Zoom in, and an angle changes. Switch symbols, and the same move may look different. I wanted to address that measurement problem.

So I chose the simplest closed shape in geometry --- the triangle --- and built a framework around it: a fixed reference point to anchor every measurement, five triangles to capture how each candle behaves from different geometric perspectives, four metrics to turn each triangle into numbers, and a coordinate system that makes those numbers more comparable across symbols, timeframes, and market conditions.

But the framework is only half the story. The other half is you.

This strategy does not predict. It does not tell you what to do. It measures --- and then it steps aside. Twenty geometric readings, raw and unfiltered, are made available to the observer. What patterns emerge from those readings, what combinations reveal structure, and what rules follow from that structure are not fixed by the code. They are developed through observation, testing, and review.

With artificial intelligence becoming part of how we study information and make decisions, I wanted to show what becomes possible when these tools meet a geometric framework. TradingView's Copilot can work alongside the chart for interactive review. CSV export makes the same active lens readings available as portable numerical data for external analysis. And TradingView's Strategy Tester closes the loop --- it takes the rules you build and reports how they would have performed historically, bar by bar, trade by trade.

This is a beginning. The twenty lenses and their combinations may reveal patterns that are not obvious from price alone --- relationships that only become visible when the right measurement lens is applied. In nature, hidden order often appears this way: Fibonacci-like spirals in sunflower heads, or fractal self-similarity in coastlines and clouds. Markets are not nature, and no analogy should be treated as proof. But the lesson is useful: sometimes a pattern becomes visible only after we build the right way to measure it.

That is how a community grows. Not from one person's answers, but from many observers bringing different eyes to the same data. Your observations, tested and shared, can become part of a map that none of us could draw alone.

One final note. My responsibility begins and ends with the design, maintenance, and continued development of this strategy. The observations you make, the configurations you build, and the trading decisions you take are entirely your own. This tool is not financial advice. It does not guarantee any outcome. It does not replace your judgment. You observe. You decide. You own the result.*

*Example: Two-Slot Configuration on BTCUSD 1h*

This configuration was built by visual observation only --- watching Pin Up Angle and Pin Down Angle on the oscillator pane and noting where spikes aligned with price reversals. No optimization was applied.

Slot 1: PnU Angle - cross > 50 - Short entry

Slot 2: PnD Angle - cross < -150 - Short exit

Minimum slots: 1 - Take-profit: 4% - No stop-loss

Signal mode: Close - Lookback: 23

Logic: enter short when the upper wick spikes above 50 degrees (ceiling rejection), exit when the lower wick drops below -150 (extreme absorption) or TP is hit.

Results (TradingView Strategy Tester, Jan 2021 --- May 2026)

107 trades - 75 winners (70.09%) - 32 losers (29.91%)

Avg win +3.45% - Avg loss -7.08% - Profit factor 0.658

Total PnL -23.85% - Max drawdown 30.70%

[![snapshot](https://www.tradingview.com/x/JWUuYxeI/)](https://www.tradingview.com/x/JWUuYxeI/)

The 70% win rate shows the geometric observation captured a recurring pattern. The negative PnL shows that without a stop-loss, the 30% of losing trades overwhelmed the capped winners. The signal found the pattern; the position management needs iteration. This used two slots, two lenses, and one side of the market. The full configuration space remains open.

3 days ago

Release Notes

*This update expands ST-Fin from a primarily geometric strategy engine into a broader analytical and execution framework. The core five-triangle ICS calculation --- frozen anchors, four metrics, and Yang-Zhang sigma normalization --- remains intact. The main changes are in display modes, smoothing and normalization, classic oscillator integration, series-vs-series comparisons, signal routing, execution controls, pyramiding, trailing exits, and debug feedback.*

1\. Three-state plot mode for every lens: OFF / Raw / MA

Each geometric lens now uses a three-state plot mode instead of a simple on/off toggle: OFF, Raw, or MA. Raw displays the original ICS output. MA displays the smoothed version using the selected moving average method.

2\. Configurable moving average: SMA / EMA / Median

A new setting in the Calculation group selects the smoothing method applied to all MA series. Three options: Simple Moving Average, Exponential Moving Average, or Median (50th percentile, robust to outliers). The MA length is shared with the Lookback period.

3\. Normalization: shared percentile-rank scale [-100, +100]

A single toggle maps all selected outputs --- geometric and classic --- to a shared percentile-rank scale of [-100, +100], making cross-metric comparison easier and more meaningful. For example, angle and area readings that normally occupy very different numeric ranges can now be read side by side. Works in combination with the MA layer.

4\. Classic oscillators: RSI, Stochastic, CCI, MACD

Four widely-used oscillators with adjustable parameters are now built in. Each one passes through the same Raw / MA / Normalize pipeline as the geometric lenses. All are available both as visual plots in the oscillator pane and as selectable variables inside the condition slots --- allowing geometric and classic signals to work together in the same rule system.

5\. Series-vs-series comparison in condition slots (Compare to)

Previously each slot could only compare its variable against a fixed numeric threshold. A new Compare to field lets any slot compare against any other live series --- geometric or classic, raw or MA. For example: Ceil angle > Flr angle, or RSI cross > RSI MA.

6\. Four new slot conditions: rising, falling, diverging, converging

Condition options grow from five to nine. Rising / falling detect whether a selected series has been rising or falling over N bars. Diverging / converging measure whether the gap between two series is widening or narrowing over N bars (requires Compare to = a series).

7\. Per-side quorum thresholds

The single shared Minimum slots required setting is replaced by four independent thresholds: Long entry, Short entry, Long exit, and Short exit. Each side of the strategy can now have its own quorum strictness.

8\. Simplified slot routing

Each slot now targets exactly one side: Long entry, Short entry, Long exit, or Short exit. The previous Both entry, Both exit, and All options have been removed. This makes slot configuration more explicit and avoids ambiguity about which side a slot is actually influencing.

9\. Automatic flip entry

A Long signal while a Short position is open automatically closes the Short and opens a Long in a single action --- and vice versa. No separate entry mode setting is needed.

10\. Pyramiding

A new Pyramid group lets the strategy add layers to an existing position when the same entry signal fires again. Controlled by an enable toggle and a Max layers setting (1--10). Each layer adds the configured equity percentage (default 5%). When disabled, only the initial entry is placed.

11\. Dual close-based trailing stop

The previous fixed SL, fixed TP, and single trailing stop have been replaced by a dual close-based trail system. Two separate thresholds: Trail profit % (tight, locks gains) and Trail loss % (wider, protects capital). Both track the best close since entry, not the high/low wick. When the position is in profit the tighter trail applies; when in loss the wider trail applies. This replaces three separate settings with a simpler, more adaptive mechanism.

12\. Observe mode and slot debug labels

A new Execution mode toggle in Chart overlay switches between Observe and Backtest. In Observe mode, no trades execute --- instead, visual debug labels appear on every bar where a signal fires. Hovering over a label shows a detailed tooltip: every active slot with its variable, condition, current value, threshold, pass/fail status, and the gap to threshold for slots that did not pass. This makes it possible to tune slot configurations visually before committing to backtest execution.

13\. Signal conflict control

When Long and Short entry signals fire on the same bar: Block both (neither enters), Long wins, or Short wins. Previously only Block both was available.

14\. Smart configuration warnings

Inverted between bounds are auto-corrected and flagged on chart. Using diverging or converging without a Compare to series triggers a warning. Alert messages now show trail percentages instead of fixed SL/TP levels.

15\. Example backtest: XAUUSD Daily, 1970--2026

To demonstrate what the new framework can do with minimal configuration, we ran a long-only setup on XAUUSD Daily using just two of the twenty available slots. No optimization was performed beyond basic risk tuning. The goal was to show a realistic, conservative baseline --- not a best-case scenario.

Configuration

Symbol: XAUUSD Daily (FXCM) --- Feb 27, 1970 to Jun 2, 2026

Initial capital: $100,000 --- Position size: 10% of equity

Signal mode: Close --- MA type: EMA --- Lookback: 23 --- Normalize: OFF

Pyramiding: OFF

Trail profit: 1.5% --- Trail loss: 3.0%

Execution mode: Backtest

Slot 1 (Long entry): Ceil angle converging Flr angle, threshold -20

Slot 2 (Long exit): Ceil angle cross < fixed value 20

Slots 3--20: OFF

Results

Total PnL: +$27,851 (+27.85%)

Max drawdown: $9,637 (8.24%)

Profitable trades: 50.91% (391 of 768)

Profit factor: 1.218

Return-to-drawdown ratio: 3.39

What this tells you

The strategy is long-only in this configuration. It enters when the ceiling and floor angles converge (the ICS framework is compressing, signaling a potential breakout), and exits when the ceiling angle drops below 20 (momentum fading). The 3% loss trail keeps drawdowns tight while the 1.5% profit trail lets winners run beyond the first bounce.

768 trades over 56 years is roughly 14 trades per year --- selective but not idle. The 8.24% max drawdown across five decades of gold history (including the 1980 crash, the 1990s sideways grind, 2013 collapse, and COVID volatility) suggests the geometric signals adapt to regime changes rather than fitting one era.

This is a starting point. The system has 20 slots, short-side capability, series-vs-series comparisons, classic oscillators, and pyramiding --- all unused in this example. The intent is to show that even a minimal two-slot setup on the ICS engine produces a tradeable edge with controlled risk.

2 days ago

Release Notes

Update --- From Strategy to Strategy Builder

The original release gave traders a geometric measurement framework --- twenty lenses from five triangles in a normalized coordinate system --- and condition slots to turn those observations into testable rules. But geometry is one dimension of the market. A trader watching a Ceiling Angle compress might also want to know whether volume confirms it, whether the close holds above the midpoint, or whether the reading has reached a level unseen in twenty bars. This update brings volume, price, and new structural conditions into the same slot system, so these questions can now be answered, combined, and backtested without leaving the settings panel.

What's new

Intrabar Volume

Buy volume, sell volume, and total volume --- computed from a configurable lower timeframe (default 1 min) --- are now available as slot variables and comparison targets. Each can be plotted Raw or MA, responds to Normalize, and combines freely with geometric lenses or classic oscillators inside any condition slot.

Price as a slot variable

Seven price series (Open, High, Low, Close, HL2, HLC3, OHLC4) are now selectable as slot variables and comparison targets. The trader can reference price levels alongside geometric readings within the same rule.

Dual comparison per slot

Each slot now supports two comparison targets (A and B) with AND / OR logic. When B is set to a series, the slot evaluates the variable against both and combines the results. When B is Fixed value, it is ignored. One slot can now express what previously required two.

Four new conditions

The condition menu grows from nine to thirteen:

Flip up / Flip down --- fires on the exact bar where a series reverses direction. No threshold or comparison needed.

New high / New low --- fires when the value exceeds its N-bar extreme (N = Threshold, min 2). Works on any series.

Streamlined settings --- 10 slots

Slots are reduced from twenty to ten. With dual comparison, four new conditions, and the expanded variable menu, each slot is more expressive than before. The settings panel is cleaner; the configuration space has grown.

Pyramid and trail exit alerts

Pyramid additions now fire their own alerts with layer number and quorum detail. Trail exits also fire alerts when the exit toggle is enabled. Every lifecycle event --- entry, pyramid, formula exit, trail exit --- is now trackable.

From strategy to strategy builder

*With volume, price, turning-point detection, and dual-comparison logic now alongside the geometric lenses and classic oscillators, the trader can express any hypothesis that spans these domains as a set of slot conditions, test it in the Strategy Tester, and refine through observation. To be precise, this is a strategy builder within a defined scope --- it works with the variables available inside the framework, not every conceivable market input. But within that scope, the number of distinct scenarios the trader can construct, test, and compare is large enough to support serious exploration.*

Example --- one slot, two worlds

On TSLA 1D with Normalize on: Slot 1 set to Vol total, cross >, Compare to RSI, Long entry. Trail profit 1.5%, loss 2%. Total volume and RSI live on different scales, but normalization maps both to [-100, +100], making their crossover a defined event. Result: profit factor 1.787, max drawdown 2.36%.

This is one signal. Nine slots remain open. A geometric filter, a price filter, a momentum condition --- each added slot refines the signal, and the Strategy Tester shows immediately whether it helped. Start with an observation, configure it, test it, layer more. Each slot is a building block. The strategy is whatever the trader decides to build.

7 hours ago

Release Notes

This update addresses several gaps in the observational layer and adds a new control mechanism to the slot system. Most of the changes came from hands-on use --- noticing where the visual feedback fell short of what the strategy actually computed, and where the trader needed more direct control over signal behavior. Nothing in the core ICS engine or geometric calculations has changed. The twenty lenses, the five triangles, and the frozen anchor logic remain exactly as before.

Observe Mode --- Full Entry→Exit Cycle Now Visible

In the previous version, Observe mode displayed entry signal labels but did not show exit points.\
This was a gap: the mode was designed to let the trader study signal behavior without executing trades --- functioning like an indicator alongside the strategy --- but without exit visibility, only half the cycle was available.\
The trader could see where entries fired, but had no way to observe where the position would have closed.

This has been corrected.\
A shadow position tracker now mirrors the full entry, exit, pyramid, and trail logic using internal state variables, independent of the strategy engine.\
When Observe mode is active, exit labels appear on the chart at the exact bars where a formula exit or trailing stop would have triggered.\
Trail thresholds are read directly from the Trail Profit and Trail Loss inputs, so the shadow behavior matches what Backtest mode would produce.\
Background shading reflects the shadow position state, completing the visual picture of the simulated trade cycle.

This brings Observe mode to parity with Backtest mode in terms of what the trader can see, compare, and evaluate.

Plot Styling --- Raw vs. MA Visual Distinction

Raw series and their moving average counterparts previously shared the same solid line style, making them difficult to tell apart when displayed together on the oscillator pane.

Raw lines now render at linewidth 2, solid.\
MA lines now render at linewidth 1, dashed.

The color of each pair remains identical --- the distinction is carried entirely by thickness and line style.\
This applies to all plot lines across the five triangle groups and the classic oscillators.

Exit Label Colors --- Entry and Exit Now Visually Separated

In the previous version, both entry and exit debug labels in Observe mode used the same green color.\
This made it difficult to distinguish entry points from exit points at a glance --- a visual deficiency that could lead to misreading the chart.

Exit labels now render in red, while entry labels remain green.\
A small correction, but one that matters for accurate observational review.

Block Slots --- Veto Logic for Entries and Exits

The slot system previously supported four signal sides:\
Long entry, Short entry, Long exit, and Short exit.

This update adds four more:\
Block long entry, Block short entry, Block long exit, and Block short exit.

A Block slot works differently from an entry or exit slot.\
Entry and exit slots use quorum logic --- a minimum number of slots must pass before the signal fires.\
A Block slot uses veto logic --- if even one active Block slot passes its condition, the corresponding signal is killed, regardless of how many entry or exit slots met their quorum.

This gives the trader a direct way to express protective conditions:\
"Do not enter short when the Floor angle is above 45 degrees."\
"Do not exit long while momentum is still rising."

The Block does not replace or compete with the entry/exit slots.\
It sits above them as a gate --- an override that prevents a signal from firing when a specific geometric condition says the timing is wrong.

When no Block slots are active, the system behaves exactly as before.\
All eight signal sides are available in every slot's Apply to dropdown.
