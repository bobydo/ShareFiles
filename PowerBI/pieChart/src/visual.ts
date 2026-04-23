"use strict";

import powerbi from "powerbi-visuals-api";
import { FormattingSettingsService } from "powerbi-visuals-utils-formattingmodel";
import * as d3 from "d3";
import "./../style/visual.less";

import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual = powerbi.extensibility.visual.IVisual;
import DataView = powerbi.DataView;

import { VisualFormattingSettingsModel } from "./settings";

type Slice = { category: string; value: number };

export class Visual implements IVisual {
    private readonly svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
    private readonly container: d3.Selection<SVGGElement, unknown, null, undefined>;
    private readonly colorScale: d3.ScaleOrdinal<string, string>;
    private readonly formattingSettingsService: FormattingSettingsService;
    private formattingSettings: VisualFormattingSettingsModel;

    constructor(options: VisualConstructorOptions) {
        this.formattingSettingsService = new FormattingSettingsService();
        this.colorScale = d3.scaleOrdinal<string, string>(d3.schemeTableau10);

        this.svg = d3.select(options.element)
            .append("svg")
            .classed("pieChart", true);
        this.container = this.svg.append("g").classed("container", true);
    }

    public update(options: VisualUpdateOptions): void {
        this.formattingSettings = this.formattingSettingsService.populateFormattingSettingsModel(
            VisualFormattingSettingsModel,
            options.dataViews[0]
        );

        const { width, height } = options.viewport;
        const radius = Math.max(0, Math.min(width, height) / 2 - 10);

        this.svg.attr("width", width).attr("height", height);
        this.container.attr("transform", `translate(${width / 2}, ${height / 2})`);

        const slices = this._extractSlices(options.dataViews?.[0]);
        if (slices.length === 0 || radius === 0) {
            this.container.selectAll("*").remove();
            return;
        }

        const arcData = d3.pie<Slice>().value(s => s.value).sort(null)(slices);
        this._renderArcs(arcData, radius);
        this._renderLabels(arcData, radius);
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel {
        return this.formattingSettingsService.buildFormattingModel(this.formattingSettings);
    }

    private _extractSlices(dataView: DataView | undefined): Slice[] {
        const categorical = dataView?.categorical;
        const categories = categorical?.categories?.[0]?.values;
        const values = categorical?.values?.[0]?.values;
        if (!categories || !values || categories.length !== values.length) {
            return [];
        }
        return categories.map((cat, i) => ({
            category: String(cat),
            value: Number(values[i]) || 0,
        }));
    }

    private _renderArcs(data: d3.PieArcDatum<Slice>[], radius: number): void {
        const arcGen = d3.arc<d3.PieArcDatum<Slice>>().innerRadius(0).outerRadius(radius);
        const sel = this.container.selectAll<SVGPathElement, d3.PieArcDatum<Slice>>("path.arc")
            .data(data, d => d.data.category);
        sel.exit().remove();
        sel.enter().append("path").classed("arc", true)
            .merge(sel)
            .attr("d", arcGen)
            .attr("fill", d => this.colorScale(d.data.category));
    }

    private _renderLabels(data: d3.PieArcDatum<Slice>[], radius: number): void {
        const labelArc = d3.arc<d3.PieArcDatum<Slice>>()
            .innerRadius(radius * 0.6)
            .outerRadius(radius * 0.6);
        const sel = this.container.selectAll<SVGTextElement, d3.PieArcDatum<Slice>>("text.label")
            .data(data, d => d.data.category);
        sel.exit().remove();
        sel.enter().append("text").classed("label", true)
            .merge(sel)
            .attr("transform", d => `translate(${labelArc.centroid(d)})`)
            .text(d => d.data.category);
    }
}
