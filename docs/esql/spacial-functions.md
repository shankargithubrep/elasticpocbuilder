---
title: ES|QL spatial functions
description: ES|QL supports these spatial functions: 
url: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/spatial-functions
---

# ES|QL spatial functions
ES|QL supports these spatial functions:
- [`ST_DISTANCE`](#esql-st_distance)
- [`ST_INTERSECTS`](#esql-st_intersects)

## `ST_DISTANCE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/st_distance.svg)

**Parameters**
<definitions>
  <definition term="geomA">
    Expression of type `geo_point` or `cartesian_point`. If `null`, the function returns `null`.
  </definition>
  <definition term="geomB">
    Expression of type `geo_point` or `cartesian_point`. If `null`, the function returns `null`. The second parameter must also have the same coordinate system as the first. This means it is not possible to combine `geo_point` and `cartesian_point` parameters.
  </definition>
</definitions>

**Description**
Computes the distance between two points. For cartesian geometries, this is the pythagorean distance in the same units as the original coordinates. For geographic geometries, this is the circular distance along the great circle in meters.
**Supported types**

| geomA           | geomB           | result |
|-----------------|-----------------|--------|
| cartesian_point | cartesian_point | double |
| geo_point       | geo_point       | double |

**Example**
```esql
FROM airports
| WHERE abbrev == "CPH"
| EVAL distance = ST_DISTANCE(location, city_location)
| KEEP abbrev, name, location, city_location, distance
```


| abbrev:k | name:text  | location:geo_point                       | city_location:geo_point | distance:d        |
|----------|------------|------------------------------------------|-------------------------|-------------------|
| CPH      | Copenhagen | POINT(12.6493508684508 55.6285017221528) | POINT(12.5683 55.6761)  | 7339.573896618216 |


